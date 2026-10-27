"""Import an environment's installed app into a new app repository branch and pull request."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode

from splunk_release import compare
from splunk_release.azure import http, log, run
from splunk_release.package import sort_confs
from splunk_release.version import (
    APP,
    CONF,
    SRC,
    TEXT,
    app_conf_version,
    bumped,
    feed_versions,
    highest,
    generate_manifest,
    git,
    set_version,
)


# Settings Splunk Cloud AppInspect rejects: the value an import writes, or None to remove the setting.
CLOUD_OFF = {"datamodels.conf": ("acceleration", "false"), "savedsearches.conf": ("action.populate_lookup", None)}


def cloud_settings_off(root):
    """Turn off or remove settings in default/ that Splunk Cloud AppInspect rejects, with one warning each."""
    from ksconf.conf.parser import write_conf
    for name, (key, off) in CLOUD_OFF.items():
        path = root / "default" / name
        conf = compare.parse(path)
        changed = [s for s, keys in conf.items()
                   if key in keys and (off is None or keys[key].strip().lower() not in ("0", "f", "false", "n", "no", "off"))]
        for stanza in changed:
            if off is None:
                del conf[stanza][key]
            else:
                conf[stanza][key] = off
            log("warning", f"default/{name} [{stanza}] {key} {'removed' if off is None else '= ' + off}: not allowed in Splunk Cloud apps")
        if changed:
            write_conf(path, conf)


def open_pull_request(branch, version, environment):
    """Create the import branch's pull request into main, set to auto-complete and delete the branch."""
    build_id = os.environ["BUILD_BUILDID"]
    source = f"refs/heads/{branch}"
    url = (
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECTID']}"
        f"/_apis/git/repositories/{os.environ['BUILD_REPOSITORY_ID']}/pullrequests"
        "?api-version=7.1"
    )
    headers = {
        "Authorization": f"Bearer {os.environ['SYSTEM_ACCESSTOKEN']}",
        "Content-Type": "application/json",
    }
    body = {
        "sourceRefName": source,
        "targetRefName": "refs/heads/main",
        "title": f"Import {APP} {version} from {environment}",
        "description": f"Created by build {build_id}.",
    }
    response = json.loads(http(url, headers, json.dumps(body).encode("utf-8")))
    complete = {
        "autoCompleteSetBy": {"id": response["createdBy"]["id"]},
        "completionOptions": {"deleteSourceBranch": True},
    }
    http(url.replace("pullrequests?", f"pullrequests/{response['pullRequestId']}?"), headers,
         json.dumps(complete).encode("utf-8"), method="PATCH")
    pull_request_url = (
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECT']}"
        f"/_git/{os.environ['BUILD_REPOSITORY_NAME']}/pullrequest/"
        f"{response['pullRequestId']}"
    )
    print(pull_request_url)


def clean_export(export_dir, destination, app, flags=(), label=None, transform=None):
    """Export, sanitize, and write an app package tree to destination; return transform's result."""
    destination = Path(destination)
    archive = Path(export_dir, f"{app}.tgz")
    if not archive.is_file():
        sys.exit(f"{label or app} export is missing {archive.name}; confirm the app is installed")

    with tempfile.TemporaryDirectory() as temp_dir:
        imported = Path(temp_dir, app)
        compare.extract(archive, imported)
        compare.merge_local(imported)
        for path in compare.files(imported):
            if compare.kept(path):
                (imported / path).unlink()
        cloud_settings_off(imported)
        for flag, folder in compare.SKIPPED.items():
            if flag in flags:
                shutil.rmtree(imported / folder, ignore_errors=True)
        if "--skip-lookups" in flags and (destination / "lookups").is_dir():
            # Keep the lookups already at destination.
            shutil.copytree(destination / "lookups", imported / "lookups")
        result = transform(imported) if transform else None
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(destination, ignore_errors=True)
        shutil.copytree(imported, destination)

    sort_confs(destination)
    return result


def import_app(environment, export_dir, *flags):
    """Replace package/ with the merged export from environment and open a pull request."""
    if set(flags) - set(compare.SKIPPED):
        sys.exit(f"Unknown option: {' '.join(flags)}")

    def set_import_version(imported):
        """Set the next patch version above package/ app.conf, or above the export's when package/ has none."""
        imported_conf = imported / "default" / "app.conf"
        current = CONF if CONF.is_file() else imported_conf
        version = bumped(highest(app_conf_version(current.read_text(**TEXT)), *feed_versions(APP.lower())), "patch")
        imported_conf.write_text(set_version(imported_conf.read_text(**TEXT), version), **TEXT)
        return version

    version = clean_export(export_dir, SRC, APP, flags, label=environment, transform=set_import_version)
    generate_manifest()
    build_id = os.environ["BUILD_BUILDID"]
    branch = f"{environment}-import/{version}-{build_id}"
    git("checkout", "-b", branch)
    git("add", "--all", str(SRC))
    git("commit", "-m", f"Import {APP} {version} from {environment}")
    git("push", "origin", f"HEAD:refs/heads/{branch}")
    open_pull_request(branch, version, environment)


def permission_request(url, headers, body=None, method=None):
    try:
        return http(url, headers, body, method=method)
    except SystemExit as error:
        if str(error.code).startswith(("HTTP 401 ", "HTTP 403 ")):
            log("warning", "Build Service permissions are required; grant them manually")
            return None
        raise


def grant_repo_permissions(collection, project, project_id, repo_id, headers):
    """Grant the project Build Service the repository permissions used by app pipelines."""
    identity_collection = collection.replace("://dev.azure.com/", "://vssps.dev.azure.com/")
    identity_query = urlencode({
        "searchFilter": "General",
        "filterValue": f"{project} Build Service",
    })
    identity_url = f"{identity_collection}_apis/identities?{identity_query}&api-version=7.1"
    identity_body = permission_request(identity_url, headers)
    if identity_body is None:
        return
    descriptor = json.loads(identity_body)["value"][0]["descriptor"]
    namespace = "2e9eb7ed-3c0a-47d4-87c1-0ffdd275fd87"
    permission_url = f"{collection}_apis/accesscontrolentries/{namespace}?api-version=7.1"
    body = {
        "token": f"repoV2/{project_id}/{repo_id}",
        "merge": True,
        "accessControlEntries": [{"descriptor": descriptor, "allow": 4 + 32 + 16384, "deny": 0}],
    }
    permission_request(permission_url, headers, json.dumps(body).encode("utf-8"))


ONBOARD_RESOURCES = [
    ("variablegroup", "splunk-appinspect"),
    ("variablegroup", "splunk-nonprod"),
    ("variablegroup", "splunk-itsi-nonprod"),
    ("variablegroup", "splunk-prod"),
    ("variablegroup", "splunk-itsi-prod"),
    ("environment", "splunk-nonprod"),
    ("environment", "splunk-prod"),
    ("repository", "tools"),
]


def onboard(app, repository, *flags):
    """Create a repository and pipeline from an exported app."""
    if set(flags) - {"--permissions"}:
        sys.exit(f"Unknown option: {' '.join(flags)}")
    repository = repository or app
    token = os.environ["SYSTEM_ACCESSTOKEN"]
    collection = os.environ["SYSTEM_COLLECTIONURI"].rstrip("/") + "/"
    project = os.environ["SYSTEM_TEAMPROJECT"]
    project_id = os.environ["SYSTEM_TEAMPROJECTID"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        clean_export(Path("export"), root / "package", app)
        example = Path(__file__).resolve().parents[1] / "example" / "azure-pipelines.yml"
        shutil.copyfile(example, root / "azure-pipelines.yml")
        try:
            repo = json.loads(http(f"{collection}{project_id}/_apis/git/repositories?api-version=7.1", headers,
                                   json.dumps({"name": repository}).encode("utf-8")))
        except SystemExit as error:
            if "already exists" in str(error.code):
                sys.exit(f"Repository {repository} already exists")
            raise
        git_in = ["git", "-C", str(root), "-c", "user.name=Azure Pipelines", "-c", "user.email=azure-pipelines@localhost"]
        run([*git_in, "init", "--initial-branch=main"], check=True)
        run([*git_in, "add", "package", "azure-pipelines.yml"], check=True)
        run([*git_in, "commit", "-m", "feat: initialize app repository"], check=True)
        run([*git_in, "remote", "add", "origin", repo["remoteUrl"]], check=True)
        run([*git_in, "-c", f"http.extraheader=AUTHORIZATION: bearer {token}", "push", "origin", "main"], check=True)

    pipeline_body = {
        "name": repository,
        "folder": "\\",
        "configuration": {
            "type": "yaml",
            "path": "/azure-pipelines.yml",
            "repository": {"id": repo["id"], "type": "azureReposGit"},
        },
    }
    pipeline = json.loads(http(f"{collection}{project_id}/_apis/pipelines?api-version=7.1", headers,
                               json.dumps(pipeline_body).encode("utf-8")))
    for resource_type, resource_name in ONBOARD_RESOURCES:
        if resource_type == "repository":
            resource_id = f"{project_id}.{os.environ['BUILD_REPOSITORY_ID']}"
        else:
            if resource_type == "variablegroup":
                resource_path = "variablegroups"
                query = {"groupName": resource_name, "api-version": "7.1"}
            else:
                resource_path = "environments"
                query = {"name": resource_name, "api-version": "7.1"}
            lookup_url = (
                f"{collection}{project_id}/_apis/distributedtask/{resource_path}?"
                f"{urlencode(query)}"
            )
            lookup = permission_request(lookup_url, headers)
            if lookup is None:
                continue
            matches = json.loads(lookup)["value"]
            if not matches:
                log("warning", f"{resource_type} {resource_name} not found; skipping pipeline authorization")
                continue
            resource_id = matches[0]["id"]
        permission_url = (
            f"{collection}{project_id}/_apis/pipelines/pipelinePermissions/"
            f"{resource_type}/{resource_id}?api-version=7.1-preview.1"
        )
        permission_body = {"pipelines": [{"id": pipeline["id"], "authorized": True}]}
        permission_request(permission_url, headers, json.dumps(permission_body).encode("utf-8"), method="PATCH")
    if "--permissions" in flags:
        grant_repo_permissions(collection, project, project_id, repo["id"], headers)
    log("section", f"Repository: {repo.get('webUrl', repo['remoteUrl'])}")
    log("section", f"Pipeline: {collection}{project_id}/_build?definitionId={pipeline['id']}")
