# azure-pipelines-splunk-apps

A shared Azure Repos pipeline for building and releasing Splunk apps. App repositories extend
`templates/splunk-app.yml`; the app source stays under `package/`.

## Flow

For a pull request targeting `main`, the pipeline:

1. Reads `[launcher] version` and `[id] version` from `package/default/app.conf` and checks that they match.
2. Fetches the target branch. If the PR version matches the target version, it bumps patch by default (or
   minor/major when the PR commit message contains `[minor]` or `[major]`), regenerates `app.manifest`, and
   commits the two files to the PR source branch. The validation run triggered by that push sees the changed
   version and skips another bump. If the version already differs or the target file is missing, it skips the
   bump.
3. Packages the app and runs AppInspect. The `appinspect-report` artifact contains the HTML and JSON reports;
   the JSON report is also printed in the job log.
4. Installs the package on the configured nonproduction stack after AppInspect passes.
5. Exports the app as installed on the production stack with the ACS app export (`default`, `local` and
   `users` content, so changes made in Splunk Web are included) and diffs it against the new package. The
   `prod-diff` artifact holds the export (`<app>-prod.tgz`) and the full diff (`prod-diff.patch`); the job
   log lists the changed files. Files under `local/` and `users/` show as present only in production. When
   the export fails, for example because the app is not in production yet, the step shows a warning and
   every package file shows as added.

After AppInspect passes on `main`, the release stage tags the commit `v<version>` and publishes the package
to the `splunk-apps` Azure Artifacts feed as `<app id>` version `<version>`. The tag push fails when that
version already tags another commit. Compare any two releases under **Repos → Tags** or **Repos → Files →
Compare**, and download any released package from **Artifacts**.

Set the template parameter `prod: true` to enable production
deployment from `main`; the `splunk-prod` environment can require approval. Pull request builds never deploy
to production. The template defaults to a Microsoft-hosted `ubuntu-latest` agent.

The build excludes dotfiles, `__pycache__`, `*.pyc`/`*.pyo`, and `tests/`. The pipeline owns both version
values and `app.manifest`.

## Files

| File | Purpose |
| --- | --- |
| `release.py` | Standard-library `bump`, `package`, `appinspect`, `deploy`, `export`, `diff` and `tag` commands; `slim` builds the manifest. |
| `templates/splunk-app.yml` | Shared build, AppInspect, and deployment stages. |
| `example/azure-pipelines.yml` | Example pipeline definition for each app repository. |
| `test_release.py` | Self-checks for version bumps, reports, the AppInspect upload and the production diff. |
| `.env.example` | Names and placeholder values for the environment variables read by `release.py`. |

## Setup

Create the shared repository and pipeline resources once per Azure DevOps project, then connect each app
repository.

### 1. Add the shared repository

Create a repository named `azure-pipelines-splunk-apps` and push this project to its `main` branch. If it is
stored in another project, update `resources.repositories[].name` in each app repository to
`<project>/azure-pipelines-splunk-apps`.

### 2. Configure the agent pool (optional)

The default pool uses `ubuntu-latest`. To use a self-hosted pool, override the `pool` parameter when extending
the template, for example:

```yaml
extends:
  template: templates/splunk-app.yml@tools
  parameters:
    pool:
      name: <agent-pool>
```

The agent needs Git, Python 3.13 in its tool cache, and outbound HTTPS access to `pypi.org`, `api.splunk.com`,
`appinspect.splunk.com`, and `admin.splunk.com`.

### 3. Create variable groups

Open **Pipelines → Library → + Variable group**. Create these groups with the exact names shown. Mark password
and token values secret.

| Group | Variable | Secret? | Value |
| --- | --- | --- | --- |
| `splunk-appinspect` | `SPLUNK_USERNAME` | no | Splunk account username |
| | `SPLUNK_PASSWORD` | yes | Splunk account password |
| `splunk-nonprod` | `SPLUNK_STACK` | no | `<stack>` |
| | `ACS_TOKEN` | yes | Admin Config Service token for `<stack>` |
| `splunk-prod` | `SPLUNK_STACK` | no | `<stack>` |
| | `ACS_TOKEN` | yes | Admin Config Service token for `<stack>` |

Create an Admin Config Service token for each target stack in Splunk Web under **Settings → Tokens**. Use an
account with the `sc_admin` role, set the audience to `acs`, and track the expiration. To identify the
experience, check **Support & Services → About** in Splunk Web.

The `proddiff` stage exports from production with the `splunk-prod` token, so that account also needs the
`export_apps` capability. `sc_admin` lacks it by default and can grant it under **Settings → Roles**.

### 4. Create deployment environments

Open **Pipelines → Environments → New environment**, choose **Resource: None**, and create:

- `splunk-nonprod`
- `splunk-prod`

Configure **Approvals and checks** on `splunk-prod` if production releases need approval. Enable production
deployment by setting `prod: true` in the app repository's template parameters.

### 5. Allow the release commit on the PR branch

The build checks out the app repository with persisted credentials and pushes the release commit to the PR
source branch. Grant the pipeline's Build Service identity **Contribute** permission on that repository or
source branch. Use the identity named like `<project> Build Service (<organization>)`; if jobs use the
collection identity, grant **Contribute** to `<organization> Project Collection Build Service (<organization>)`.

Each `main` build also pushes the `v<version>` tag, so grant the same identity **Create tag** on the
repository.

### 6. Create the release feed

Open **Artifacts → Create Feed**, name it `splunk-apps` and scope it to the project. Under **Feed settings →
Permissions**, give the Build Service identity the **Feed Publisher (Contributor)** role.

### 7. Add the main branch build validation policy

Azure Repos does not use YAML `pr:` triggers. In the app repository, open **Repos → Branches → main → Branch
policies → Build validation**, add this pipeline, and configure it as required or optional with the desired
automatic queue behavior. This policy starts the PR validation run. The example YAML separately triggers
commits to `main`.

### 8. Connect each app repository

An app repository has this shape:

```text
<app-repo>/
├── azure-pipelines.yml
└── package/
    └── default/app.conf
```

`package/default/app.conf` needs matching versions in `[launcher]` and `[id]`:

```ini
[id]
name = <app-id>
version = 1.0.0

[launcher]
version = 1.0.0

[package]
id = <app-id>
```

Copy `example/azure-pipelines.yml` to the app repository. Then create a pipeline using
**Pipelines → New pipeline → Azure Repos Git → Existing Azure Pipelines YAML file → `/azure-pipelines.yml`**.
Permit access to the shared repository, variable groups, and environments when prompted. A pull request runs
**build → appinspect → nonprod → proddiff**; a `main` build runs **build → appinspect → release**, and also
**prod** when enabled.

For another target branch, change the `main` values in both the `trigger` and branch policy configuration.

## Local use

From an app repository root:

```sh
pip install splunk-packaging-toolkit
python <path-to>/azure-pipelines-splunk-apps/release.py package
python <path-to>/azure-pipelines-splunk-apps/test_release.py
```

`release.py bump` is intended for PR validation builds. `release.py appinspect <dir>` writes
`appinspect-report.html` and `appinspect-report.json` alongside the package. `release.py deploy <dir>` uploads
the package to a Victoria stack using ACS. `release.py export <dir>` saves the installed app from the stack in
`SPLUNK_STACK`, and `release.py diff <pkg-dir> <dir>` writes the diff against a package.
`release.py tag` is intended for `main` builds.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `[launcher] and [id] need the same version` | Set both `version` values in `app.conf` to the same `x.y.z`. |
| `version already changed, skipping bump` | Expected after the release commit reaches the PR branch, or when the PR already set the version. |
| `target app.conf is missing, skipping bump` | Add `package/default/app.conf` on the PR target branch. |
| `git push` fails (`TF401027` / `TF402455`) | Grant the pipeline Build Service **Contribute** on the PR source branch. |
| HTTP 401 from `api.splunk.com` | Check `SPLUNK_USERNAME` and `SPLUNK_PASSWORD` in `splunk-appinspect`. |
| AppInspect fails | Download the `appinspect-report` artifact and review its HTML or JSON report. |
| HTTP 401/403 from `admin.splunk.com` | Check that `ACS_TOKEN` is valid, has the `acs` audience, and belongs to an account with `sc_admin`. |
| HTTP 404 from `admin.splunk.com` | Check `SPLUNK_STACK`. |
| Production stage does not run | Set `prod: true`, and confirm the build came from `refs/heads/main`. |
| Run waits on “needs permission” | Permit the shared repository, variable groups, and environments for the pipeline. |

## License

[Apache License 2.0](LICENSE)
