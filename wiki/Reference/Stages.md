# Stages

Use this page to find each app pipeline stage in run order. The last three sections describe the steps and
stages that other pipelines share.

| Order | Stage | Display name | Runs when |
| --- | --- | --- | --- |
| 1 | `build` | Build | Every run |
| 2 | `appinspect` | AppInspect | After `build`, unless the build pushed a version bump |
| 3 | `nonproddiff` | Compare with nonprod | Pull request or `main` |
| 4 | `nonprod` | Deploy to nonprod | Pull request or `main`, after `nonproddiff` |
| 5 | `proddiff` | Compare with prod | Pull request or `main`, after `nonprod` |
| 6 | `release` | Release | `main`, after `proddiff` |
| 7 | `prod` | Deploy to prod | `main`, after `release`, after approval |

The import stages, `import_nonprod` and `import_prod`, run only when an import option is selected. See
[App: Import](/Pipelines/App#import).

## Build

![Build stage.](../diagrams/build-stage.png)

Stage `build`:

- **Does:** plans the run, sorts and packages the app, and bumps the version on a pull request when the target
  branch has not changed it.
- **Inputs:** app repo, tools repo, Python 3.13, the build reason and branch variables, `slim`, `ksconf`, and the
  Splunk SDK.
- **Outputs:** the `dist` pipeline artifact, which holds the app package.

Job `build` runs on the selected `pool`. It produces the `dist` artifact. After a successful pull request bump,
it also pushes a commit to the pull request source branch.

### Version bump rules

`release.py bump` changes versions only on pull request runs. It does so only when the source and target version
rows match, and the target branch has not changed the version. `[major]` increments the major version and resets
minor and patch. `[minor]` increments the minor version and resets patch to zero. Otherwise, the patch number
increments. The bump starts from the highest of the target version and every version in the splunk-apps feed. It
therefore always goes above a version that the [Repair pipeline](/Pipelines/Repair) published. The bump updates
`version` in `[launcher]` and `[id]`, regenerates `app.manifest`, commits both files, and pushes the commit to the
pull request source branch.

Steps, in order:

- **Checkout app (`checkout: self`):** gets the app repo at `app`, and keeps credentials for the bump push.
- **Checkout tools (`checkout: tools`, default `setup`):** gets the shared scripts.
- **UsePythonVersion@0 (default `setup`):** selects Python 3.13.
- **Use UTF-8 for Python files and output (default `setup`):** sets `PYTHONUTF8=1` for later steps.
- **Show stage plan:** prints each stage and its run condition, from the build reason and source branch.
- **Install diff dependencies:** installs pinned `ksconf` and Splunk SDK packages from `templates/diff-tools.yml`.
- **Install packaging toolkit:** the shared dependency template adds the packaging toolkit, `slim`, for build and
  import jobs.
- **Bump PR version and manifest:** on pull request runs, sorts config files, checks the target version, updates
  the matching version fields and the manifest, commits, and pushes to the source branch. After a push it sets
  `bump.bumped`. Package app, Publish artifact, and every later stage then skip in that run. The bump commit starts
  the next validation run. If the bump is skipped, the step prints the reason.
- **Package app:** sorts config files, stages the app, and creates the package under `dist/`. `.meta` files list
  `[]` first, then stanzas without `/`, then stanzas with `/`. Each group is in name order.
- **Publish artifact (`publish: dist`):** publishes the package directory as the `dist` artifact.

## AppInspect

Stage `appinspect`:

- **Does:** runs after `build`. Only a passing result allows the later stages.
- **Inputs:** `dist`, Python 3.13, the `splunk-appinspect` group, the AppInspect credentials, and the AppInspect
  service.
- **Outputs:** the AppInspect result, and the `appinspect-report-<attempt>` artifact.

Job `appinspect` submits the package and reads its validation reports. It maps `SPLUNK_PASSWORD` into the script
environment. The unlocked `SPLUNK_USERNAME` is available to the script.

Steps, in order:

- **Checkout tools (`checkout: tools`, default `setup`):** gets the shared scripts.
- **UsePythonVersion@0 (default `setup`):** selects Python 3.13.
- **Use UTF-8 for Python files and output (default `setup`):** sets `PYTHONUTF8=1`.
- **Download artifact (`download: current`, `dist`):** retrieves the app package into the workspace.
- **Run AppInspect:** validates the package with the `private_victoria` and `future` tags. It writes JSON and HTML
  reports, and sets pass or fail. It warns for each `future_failure` check. The log prints the summary in two
  sections. **Blocks deployment** lists `status`, `error`, `failure`, and `manual_check`. **Does not block
  deployment** lists every other count.
- **Collect AppInspect reports (`CopyFiles@2`):** copies the reports, even when validation failed.
- **Publish artifact (`appinspect-report-$(System.JobAttempt)`):** publishes the reports for this job attempt.
- **Show AppInspect JSON report:** prints the JSON report when the job succeeded or failed.
- **Show AppInspect HTML report link:** prints the link to the run's published artifact, even when the job failed.

## Nonproddiff

Stage `nonproddiff`, displayed as **Compare with nonprod**:

- **Does:** runs after AppInspect on pull requests and `main` runs.
- **Inputs:** the `dist` package, the `splunk-nonprod` group, and the `splunk-itsi-nonprod` group.
- **Outputs:** the `nonprod-diff-<app-id>-<attempt>` and `itsi-nonprod-diff-<app-id>-<attempt>` artifacts.

Jobs run in parallel and install nothing:

- `compare_nonprod`, displayed as **Compare with nonprod**, uses `splunk-nonprod`.
- `compare_itsi_nonprod`, displayed as **Compare with itsi-nonprod**, uses `splunk-itsi-nonprod`.

Each job runs the package steps, installs the diff tools, and sets up the ACS CLI. It then checks the stack status,
exports the installed app, and runs the [compare steps](#compare-steps).

## Nonprod

Stage `nonprod`, displayed as **Deploy to nonprod**:

- **Does:** runs after `nonproddiff` on pull requests and `main` runs.
- **Inputs:** the `dist` package, the groups `splunk-appinspect` and `splunk-nonprod`, and the `splunk-nonprod`
  environment.
- **Outputs:** the app installed through ACS.
- **Lock:** sequential.

Job `deploy`, displayed as **Install on nonprod**, sets up the ACS CLI and installs the package. It does not
compare the package with nonprod. It checks the stack status before and after the deployment. The shared deploy
template can uninstall the app before installation when that is enabled.

## Proddiff

Stage `proddiff`, displayed as **Compare with prod**:

- **Does:** runs after `nonprod` on pull requests and `main` runs.
- **Inputs:** the `dist` package, the `splunk-prod` group, and the `splunk-itsi-prod` group.
- **Outputs:** the `prod-diff-<app-id>-<attempt>` and `itsi-prod-diff-<app-id>-<attempt>` artifacts.

Jobs `compare_prod` and `compare_itsi_prod` run in parallel. They display as **Compare with prod** and
**Compare with itsi-prod**. They do not install the package. Each one runs the package steps, installs the diff
tools, sets up the ACS CLI, checks the stack status, and exports the installed app. Then it runs the
[compare steps](#compare-steps).

## Release

Stage `release`:

- **Does:** runs after `proddiff` on `refs/heads/main`.
- **Inputs:** `dist`, the app repo checkout, the repository credentials, and the `splunk-apps` package feed.
- **Outputs:** the version tag, and the Universal Package in the feed.

Job `release` tags the app commit and publishes the package. Its steps, in order:

- **Checkout app (`checkout: self`):** gets the app repo, and keeps credentials for the tag push.
- **Checkout tools (`checkout: tools`, default `setup`):** gets the shared scripts.
- **UsePythonVersion@0 (default `setup`):** selects Python 3.13.
- **Use UTF-8 for Python files and output (default `setup`):** sets `PYTHONUTF8=1`.
- **Download artifact (`download: current`, `dist`):** gets the package into the workspace.
- **Tag the release version:** creates and pushes `v<version>`, and sets `APP_ID` and `APP_VERSION`. When the feed
  already holds that version, it prints `<app-id> <version> is already in the splunk-apps feed, skipping publish`
  and sets `PACKAGE_PUBLISHED`.
- **Upload the package to the splunk-apps feed (`UniversalPackages@0`):** uploads the package. It is skipped when
  `PACKAGE_PUBLISHED` is `true`.

## Prod

Stage `prod`, displayed as **Deploy to prod**:

- **Does:** runs after **Release**, on successful `refs/heads/main` runs.
- **Inputs:** `dist`, the groups `splunk-appinspect` and `splunk-prod`, and the `splunk-prod` environment.
- **Outputs:** the app installed through ACS. The [Proddiff stage](#proddiff) holds the prod compare for the run.
- **Approval:** waits for the `splunk-prod` Approvals check. Nothing installs without approval. A rejection stops the
  stage. If approval reaches its Timeout, Azure marks the stage skipped.
- **Lock:** sequential. The Exclusive Lock check runs after the approvals, so waiting for approval does not hold the
  prod lock.

Job `deploy`, displayed as **Install on prod**, installs the package through ACS and waits for the version. It checks
the stack status. It does not repeat the compare.

## Compare steps

The app compare stages and the deploy compare stages run these four steps. The Compare pipeline's `compare` job runs
the same four steps, with the target compared against the source.

- **Compare `<side>` with this package (file tree, local and default):** writes `<app-id>-tree.txt`, the raw file
  changes.
- **Compare `<side>` with this package (local files vs default):** writes the local-versus-default report.
- **Compare `<side>` with this package (merged defaults):** writes the patch, the summary, the HTML report, and the
  merged archive.
- **Compare `<side>` with this package (data models):** writes the data model patch. It prints each changed data
  model in its own collapsed group.

Each compare job publishes `<side>-diff-<app-id>-<attempt>` with its reports. The reports are described in
[Artifacts](/Reference/Artifacts).

## Bulk stage

Used by the [bulk install, update, and delete pipelines](/Pipelines/Bulk-Install).

- **Stage:** `bulk`, displayed as `Bulk <action> <type> on <environment>`.
- **Job:** deployment job, displayed as `Run ACS bulk <action> for <type>`. It runs on the `splunk-<environment>`
  environment, so `splunk-prod` runs wait for its approval. It uses the `splunk-appinspect` group and the
  `splunk-<environment>` group. Its lock is sequential.
- **Steps:** check out the tools, select Python 3.13, set up the ACS CLI. For `splunkbase-apps` installs, it first
  runs `bulk-fetch-license`. Then it runs the ACS bulk command for the action and type.
- **Credentials:** the Splunkbase commands use the splunk.com account from `splunk-appinspect`, mapped to
  `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- **Results:** each bulk command tries every item, and prints success and failure counts.
- **Restart:** when the `restart` option is on, a [restart stage](#restart-stage) runs after the bulk stage.

## Restart stage

Used by the [Deploy pipeline](/Pipelines/Deploy) after the uninstalls and the installs, and by the bulk pipelines
after a bulk action.

- **Does:** restarts the ITSI search head first, then the main search head, of one environment. Each job restarts
  only when ACS reports that a restart is required, then checks the stack status.
- **Environment:** the `splunk-<environment>` deployment environment, so the restart waits for its approval.
- **Lock:** sequential.
