"""Import an environment's installed app into a new app repository branch and pull request."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from splunk_release import compare
from splunk_release.acs import export, require_private
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


# app.conf [install] settings Splunk Cloud AppInspect rejects.
INSTALL_REMOVED = ("install_source_checksum", "install_source_local_checksum", "state_change_requires_restart")


def app_conf_required(root, app):
    """Set the app.conf settings Splunk Cloud AppInspect requires, with one warning each."""
    from ksconf.conf.parser import write_conf
    path = root / "default" / "app.conf"
    conf = compare.parse(path)
    versions = [conf[stanza]["version"] for stanza in ("id", "launcher") if conf.get(stanza, {}).get("version")]
    label = conf.get("ui", {}).get("label", "")
    required = {
        ("id", "name"): app,
        ("id", "version"): highest(*versions) if versions else "1.0.0",
        ("package", "id"): app,
        ("package", "check_for_updates"): "false",
        ("ui", "label"): label if 5 <= len(label) <= 80 else (app if len(app) >= 5 else f"{app} app")[:80],
    }
    required["launcher", "version"] = required["id", "version"]
    if conf.get("install", {}).get("is_configured", "").strip().lower() in ("1", "t", "true", "y", "yes", "on"):
        required["install", "is_configured"] = "false"
    changed = False
    for (stanza, key), value in required.items():
        if conf.get(stanza, {}).get(key) != value:
            conf.setdefault(stanza, {})[key] = value
            log("warning", f"default/app.conf [{stanza}] {key} = {value}: required by Splunk Cloud AppInspect")
            changed = True
    for key in INSTALL_REMOVED:
        if key in conf.get("install", {}):
            del conf["install"][key]
            log("warning", f"default/app.conf [install] {key} removed: not allowed in Splunk Cloud apps")
            changed = True
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
        app_conf_required(imported, app)
        for flag, folder in compare.SKIPPED.items():
            if flag in flags:
                shutil.rmtree(imported / folder, ignore_errors=True)
        if "--skip-lookups" in flags and (destination / "lookups").is_dir():
            # Keep the lookups already at destination.
            shutil.copytree(destination / "lookups", imported / "lookups")
        shutil.rmtree(imported / compare.BACKUPS, ignore_errors=True)
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
            log("warning", f"{str(error.code)[:8]} from {url.split('?')[0]}: give the Build Service the Administrator "
                           "role on this resource, or add the new pipeline to its Pipeline permissions")
            return None
        raise


# Variable groups and environments the app pipeline uses; onboard also authorizes the tools repository.
ONBOARD_RESOURCES = [
    *(("variablegroup", f"variablegroups?groupName={name}") for name in
      ("splunk-appinspect", "splunk-nonprod", "splunk-itsi-nonprod", "splunk-prod", "splunk-itsi-prod")),
    *(("environment", f"environments?name={name}") for name in ("splunk-nonprod", "splunk-prod")),
]


def onboard(app):
    """Export a private app into its repository's empty package/ and create its pipeline, both named after the app."""
    token = os.environ["SYSTEM_ACCESSTOKEN"]
    collection = os.environ["SYSTEM_COLLECTIONURI"].rstrip("/") + "/"
    project_id = os.environ["SYSTEM_TEAMPROJECTID"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    repo = json.loads(http(f"{collection}{project_id}/_apis/git/repositories/{app}?api-version=7.1", headers))
    auth = f"http.extraheader=AUTHORIZATION: bearer {token}"
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        git_in = ["git", "-C", str(root), "-c", "user.name=Azure Pipelines", "-c", "user.email=azure-pipelines@localhost"]
        if repo.get("defaultBranch"):
            run(["git", "-c", auth, "clone", "-q", repo["remoteUrl"], str(root)], check=True)
            if any(path.is_file() and path.name != ".gitkeep" for path in (root / "package").rglob("*")):
                sys.exit(f"Repository {app} already has files in package/. Onboard needs an empty package/")
        else:
            run([*git_in, "init", "--initial-branch=main"], check=True)
            run([*git_in, "remote", "add", "origin", repo["remoteUrl"]], check=True)
        require_private(app)
        export("export", app)
        shutil.rmtree(root / "package", ignore_errors=True)
        clean_export(Path("export"), root / "package", app)
        if not (root / "azure-pipelines.yml").exists():
            example = Path(__file__).resolve().parents[1] / "example" / "azure-pipelines.yml"
            shutil.copyfile(example, root / "azure-pipelines.yml")
        run([*git_in, "add", "package", "azure-pipelines.yml"], check=True)
        run([*git_in, "commit", "-m", f"feat: onboard {app}"], check=True)
        run([*git_in, "-c", auth, "push", "origin", "HEAD:main"], check=True)

    pipeline_body = {
        "name": app,
        "folder": "\\",
        "configuration": {
            "type": "yaml",
            "path": "/azure-pipelines.yml",
            "repository": {"id": repo["id"], "type": "azureReposGit"},
        },
    }
    pipeline = json.loads(http(f"{collection}{project_id}/_apis/pipelines?api-version=7.1", headers,
                               json.dumps(pipeline_body).encode("utf-8")))
    resources = []
    for resource_type, query in ONBOARD_RESOURCES:
        found = permission_request(f"{collection}{project_id}/_apis/distributedtask/{query}&api-version=7.1", headers)
        matches = json.loads(found)["value"] if found else []
        if matches:
            resources.append((resource_type, matches[0]["id"]))
        elif found:
            log("warning", f"{query} not found; select Permit on the first run")
    resources.append(("repository", f"{project_id}.{os.environ['BUILD_REPOSITORY_ID']}"))
    body = json.dumps({"pipelines": [{"id": pipeline["id"], "authorized": True}]}).encode("utf-8")
    for resource_type, resource_id in resources:
        permission_request(f"{collection}{project_id}/_apis/pipelines/pipelinePermissions/{resource_type}/"
                           f"{resource_id}?api-version=7.1-preview.1", headers, body, method="PATCH")
    log("section", f"Repository: {repo.get('webUrl', repo['remoteUrl'])}")
    log("section", f"Pipeline: {collection}{project_id}/_build?definitionId={pipeline['id']}")
