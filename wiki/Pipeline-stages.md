# Pipeline stages

[[_TOC_]]

This page follows the checked-in YAML. Steps use their `displayName` when
present. For steps without one, the entry names the YAML action or task.
The shared template defaults to Python 3.13 and checks out the tools repo.
An app repo can override the `setup` and `pool` parameters.

## Main app pipeline

The shared template has `build` and `appinspect` stages on every run. Pull
request and `refs/heads/main` runs continue through `nonprod` and `proddiff`.
Runs from `refs/heads/main` also continue through `release`. Production
installation uses the separate manual deploy pipeline.

### Stage `build`

- **Does:** Plans the run, sorts and packages the app, and bumps the version
  on a pull request when the target branch has not changed it.
- **Inputs:** App repo, tools repo, Python 3.13, build reason and branch
  variables, `slim`, `ksconf`, and Splunk SDK packages.
- **Outputs:** `dist` pipeline artifact containing the app package.

#### Job `build` in the build stage

- **Does:** Runs on the selected `pool` and prepares the package for later
  stages.
- **Inputs:** App repo; tools repo; `Build.Reason`, `Build.SourceBranch`, and
  default `setup` or the app repo override.
- **Outputs:** `dist` artifact and, for a successful pull request bump, a
  commit pushed to the pull request source branch.

Steps, in order:

- **Checkout app (`checkout: self`):** Gets the app repo at `app` and keeps
  credentials for the bump push. **Inputs:** App repo revision.
  **Outputs:** `$(Pipeline.Workspace)/app` checkout.
- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Show stage plan:** Prints each stage and its run condition.
  **Inputs:** Build reason and source branch.
  **Outputs:** Stage plan in the job log.
- **Install slim and ksconf:** Installs the packaging, sorting, and SDK
  packages. **Inputs:** Python package index. **Outputs:** `slim`, `ksconf`,
  and Splunk SDK in the Python environment.
- **Bump PR version and manifest:** On pull request runs, sorts config files,
  checks the target version, updates matching version fields and manifest,
  commits, then pushes to the source branch. **Inputs:** App files, target
  and source refs, commit message, and repository credentials.
  **Outputs:** Updated source branch or a printed skip reason.
- **Package app:** Sorts config files, stages the app, and creates the
  package. **Inputs:** `package/` and installed packaging tools.
  **Outputs:** Package under `dist/`.
- **Publish artifact (`publish: dist`):** Publishes the package directory.
  **Inputs:** `$(Pipeline.Workspace)/app/dist`. **Outputs:** `dist` pipeline
  artifact.

### Stage `appinspect`

- **Does:** Runs after `build`; only a passing result allows later stages.
- **Inputs:** `dist`, Python 3.13, `splunk-appinspect`, AppInspect credentials,
  and the AppInspect service.
- **Outputs:** AppInspect result and `appinspect-report-<attempt>` artifact.

#### Job `appinspect` in the appinspect stage

- **Does:** Submits the package and reads its validation reports.
- **Inputs:** `splunk-appinspect` variable group, `dist` artifact, tools repo,
  Python 3.13, and `SPLUNK_PASSWORD` mapped into the script environment.
  The unlocked `SPLUNK_USERNAME` variable is available to the script.
- **Outputs:** Pass or fail result; report files when the service returns them.

Steps, in order:

- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Download artifact (`download: current`, `dist`):** Retrieves the app
  package. **Inputs:** `dist` artifact. **Outputs:** `dist/` in the workspace.
- **Run AppInspect:** Validates the package with `private_victoria` and
  `future` tags. **Inputs:** Package, username, and mapped password.
  **Outputs:** JSON and HTML reports, pass/fail status, and a warning for
  `future_failure` checks.
- **Collect AppInspect reports (`CopyFiles@2`):** Copies matching reports
  even when the validation step failed. **Inputs:** `dist/appinspect-report.*`.
  **Outputs:** `appinspect-report/` in the workspace.
- **Publish artifact (`appinspect-report-$(System.JobAttempt)`):** Publishes
  the reports for this job attempt. **Inputs:** Collected report directory.
  **Outputs:** Attempt-named pipeline artifact.
- **Show AppInspect JSON report:** Prints the JSON report when the job has
  succeeded or failed. **Inputs:** JSON report file. **Outputs:** Report JSON
  in the log.
- **Show AppInspect HTML report link:** Prints the run's published-artifact
  link even when the job failed. **Inputs:** Collection URI, project id, and
  build id. **Outputs:** Link in the log.

### Stage `nonprod`

- **Does:** Runs after a successful AppInspect stage on a pull request or
  `refs/heads/main` run.
- **Inputs:** `dist`, `splunk-appinspect` and `splunk-nonprod` groups, and the
  `splunk-nonprod` environment.
- **Outputs:** Nonprod diff artifact and app installation through ACS.

#### Deployment job `deploy` in the nonprod stage

- **Does:** Uses `templates/deploy.yml` to export, compare, and install the
  package in the `splunk-nonprod` environment.
- **Inputs:** `dist`, groups `splunk-appinspect` and `splunk-nonprod`, Python
  setup, `SPLUNK_STACK`, `ACS_TOKEN`, and AppInspect username/password.
- **Outputs:** `nonprod-diff-<attempt>` artifact and installed private app.

The deployment job installs Python, ACS CLI, and diff dependencies once, then
downloads `dist`. `templates/deploy.yml` runs these steps for the package:

- **Check stack status:** Reports current status and warns if restart is
  required. **Inputs:** Nonprod ACS session.
- **Export the app from nonprod via ACS:** Gets the app id from the package
  filename and exports the installed app.
  **Inputs:** `SPLUNK_STACK` and mapped `ACS_TOKEN` as `STACK_TOKEN`.
  **Outputs:** `nonprod-export/`.
- **Compare nonprod with this package:** Writes local, patch, summary, and
  merged archive reports. **Inputs:** Nonprod export and `dist` package.
  **Outputs:** `nonprod-diff/`.
- **Publish artifact (`nonprod-diff-<app>-$(System.JobAttempt)`):** Publishes
  this app's diff. **Inputs:** App diff directory. **Outputs:** Attempt-named
  pipeline artifact.
- **Deploy to nonprod via ACS:** Installs the package as a private app.
  **Inputs:** `dist`, `SPLUNK_USERNAME`, `SPLUNK_PASSWORD`, `SPLUNK_STACK`,
  and `ACS_TOKEN` mapped to `STACK_TOKEN`. **Outputs:** App install result.
- **Wait for the deployed version:** Checks `acs apps describe` every three
  seconds for up to 300 seconds. **Inputs:** Package version and ACS session.
  **Outputs:** Confirmed app version or a timeout error.
- **Check stack status after deploy:** Prints current stack status and warns
  if a restart is required. **Inputs:** Nonprod ACS session.

### Stage `proddiff`

- **Does:** Runs after `nonprod` succeeds on a pull request or
  `refs/heads/main` run.
- **Inputs:** `dist`, `splunk-prod`, tools repo, and Python setup.
- **Outputs:** `prod-diff-<attempt>` artifact for review.

#### Job `proddiff` in the proddiff stage

- **Does:** Exports the production app and compares it with the package.
- **Inputs:** `splunk-prod` group, `SPLUNK_STACK`, `ACS_TOKEN`, `dist`, and
  Python 3.13.
- **Outputs:** `prod-diff-<attempt>` pipeline artifact.

Steps, in order:

- **Checkout app (`checkout: self`):** Gets the app repo at `app`.
  **Inputs:** App repo revision. **Outputs:** App checkout.
- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Download artifact (`download: current`, `dist`):** Gets the package.
  **Inputs:** `dist` artifact. **Outputs:** `dist/` in the workspace.
- **Install ACS CLI 2.26.0:** Downloads, verifies, and unpacks the CLI.
  **Inputs:** Agent OS, `curl`, GitHub release file, and checksum.
  **Outputs:** `acs` on `PATH`.
- **ACS CLI version:** Prints the installed CLI version.
  **Inputs:** `acs` on `PATH`. **Outputs:** Version in the log.
- **Export the app from production via ACS:** Exports the configured app.
  **Inputs:** `SPLUNK_STACK` and mapped `ACS_TOKEN` as `STACK_TOKEN`.
  **Outputs:** `prod-export/`.
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Diff production against this package:** Compares exports and writes
  review files. **Inputs:** `prod-export/` and `dist/`. **Outputs:**
  `prod-diff/`.
- **Publish artifact (`prod-diff-$(System.JobAttempt)`):** Publishes this
  attempt's reports. **Inputs:** `prod-diff/`. **Outputs:** Attempt-named
  pipeline artifact.

### Stage `release`

- **Does:** Runs after AppInspect on `refs/heads/main`.
- **Inputs:** `dist`, app repo checkout, repository credentials, and the
  `splunk-apps` package feed.
- **Outputs:** Version tag and Universal Package in the feed.

#### Job `release` in the release stage

- **Does:** Tags the app commit and publishes the package.
- **Inputs:** `dist`, app repo, Python setup, `APP_ID`, and `APP_VERSION`.
- **Outputs:** `v<version>` tag and package named by app id and version.

Steps, in order:

- **Checkout app (`checkout: self`):** Gets the app repo and keeps credentials
  for tag push. **Inputs:** App repo revision. **Outputs:** App checkout.
- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Download artifact (`download: current`, `dist`):** Gets the package.
  **Inputs:** `dist` artifact. **Outputs:** `dist/` in the workspace.
- **Tag the release version:** Creates and pushes `v<version>`; sets
  `APP_ID` and `APP_VERSION`. **Inputs:** App version and repo credentials.
  **Outputs:** Git tag and pipeline variables.
- **Publish the package to the splunk-apps feed (`UniversalPackages@0`):**
  Publishes the package. **Inputs:** `dist/`, `APP_ID`, `APP_VERSION`, and
  feed permissions. **Outputs:** Universal Package in the feed.

## Manual deploy pipeline

The pipeline in `deploy/azure-pipelines.yml` accepts an environment and
space-separated app ids. It uses the matching `splunk-<environment>` group
and deployment environment, so configured approvals apply. For each app it
downloads the latest package from `splunk-apps` and runs
`templates/deploy.yml`. After all packages succeed, it restarts the stack and
checks status.

The deploy job checks out the tools repo, selects Python 3.13, installs the
ACS CLI and diff dependencies once, then runs the shared steps for each app:

- Check status and export the installed app.
- Create and publish `<environment>-diff-<app>-<attempt>`.
- Install the package, wait for its version, and check status again.

## Restart pipeline

The manual restart pipeline selects `nonprod` or `prod` and group prefix
`splunk` or `splunk-itsi`. It checks status, restarts the current stack,
polls until `restartRequired` is false, and checks status again.

The restart job uses `workspace: clean: all`, Python 3.13, the shared ACS CLI
template, and the selected variable group. ACS steps map `ACS_TOKEN` to
`STACK_TOKEN` and pass the optional `SPLUNK_SEARCH_HEAD` value.

## Compare pipeline

The manual pipeline selects `source` and `target` environments, each
`nonprod` or `prod`, and a `groupPrefix` of `splunk` or `splunk-itsi`. The
default source is nonprod and the default target is prod. An empty `apps`
parameter exports every custom app from both environments. Otherwise, it
exports the listed app ids. The compare job diffs target against source.

### Jobs `source` and `target` in the compare pipeline

- **Does:** Exports the selected app ids from the selected environment.
- **Inputs:** `groupPrefix`, environment, `SPLUNK_STACK`,
  `SPLUNK_SEARCH_HEAD`, `ACS_TOKEN`, and `apps`.
- **Outputs:** `<environment>-export` artifact.

Each job selects Python 3.13 and installs ACS CLI 2.26.0 through the shared
template. It calls either `release.py export` or `release.py export --custom`,
then publishes its export directory.

### Job `compare` in the compare pipeline

- **Does:** Waits for both export jobs and compares target to source.
- **Inputs:** Source and target export artifacts, Python 3.13, `ksconf`, and
  Splunk SDK.
- **Outputs:** `compare` artifact.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Download artifacts (`download: current`):** Gets current-run exports.
  **Inputs:** Published artifacts. **Outputs:** Export directories.
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Compare target with source:** Writes per-app reports.
  **Inputs:** Target and source exports. **Outputs:**
  `$(Pipeline.Workspace)/compare`.
- **Upload summary:** Adds each Markdown summary to the run summary tab.
  **Inputs:** Per-app summary paths. **Outputs:** Run summary entries.
- **Publish artifact (`compare`):** Publishes the reports.
  **Inputs:** HTML diff, patch, summary, local comparison, and merged archive.
  **Outputs:** `compare` artifact.

## Smoke-test pipeline

The manual pipeline checks AppInspect login and read-only ACS access for
target `splunk` or `splunk-itsi`. The final job reports all three results.

### Job `appinspect` in the smoke-test pipeline

- **Does:** Checks AppInspect credentials.
- **Inputs:** `splunk-appinspect`, Python 3.13, `SPLUNK_USERNAME`, and
  `SPLUNK_PASSWORD`.
- **Outputs:** Login result.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Check AppInspect credentials:** Requests a login token.
  **Inputs:** Username and mapped password. **Outputs:** PASS or login error.

### Job `nonprod` in the smoke-test pipeline

- **Does:** Checks ACS login, app listing, and export access.
- **Inputs:** Nonprod group, Python 3.13, and `SPLUNK_STACK`,
  `SPLUNK_SEARCH_HEAD`, and `ACS_TOKEN`.
- **Outputs:** Login, app list, and export result.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Install ACS CLI 2.26.0:** Downloads and verifies the CLI.
  **Inputs:** Agent OS, `curl`, release file, checksum. **Outputs:** `acs` on
  `PATH`.
- **ACS CLI version:** Prints the installed version. **Inputs:** `acs` on
  `PATH`. **Outputs:** Version in the log.
- **Check nonprod ACS access and export:** Lists apps and exports only the
  built-in search app's local and user configuration files.
  **Inputs:** Nonprod group, `SPLUNK_STACK`, optional
  `SPLUNK_SEARCH_HEAD`, and `ACS_TOKEN`. **Outputs:** PASS lines or an error.

### Job `prod` in the smoke-test pipeline

- **Does:** Checks ACS login, app listing, and export access.
- **Inputs:** Prod group, Python 3.13, and `SPLUNK_STACK`,
  `SPLUNK_SEARCH_HEAD`, and `ACS_TOKEN`.
- **Outputs:** Login, app list, and export result.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Install ACS CLI 2.26.0:** Downloads and verifies the CLI.
  **Inputs:** Agent OS, `curl`, release file, checksum. **Outputs:** `acs` on
  `PATH`.
- **ACS CLI version:** Prints the installed version. **Inputs:** `acs` on
  `PATH`. **Outputs:** Version in the log.
- **Check prod ACS access and export:** Lists apps and exports only the
  built-in search app's local and user configuration files.
  **Inputs:** Prod group, `SPLUNK_STACK`, optional
  `SPLUNK_SEARCH_HEAD`, and `ACS_TOKEN`. **Outputs:** PASS lines or an error.

### Job `result` in the smoke-test pipeline

- **Does:** Runs after all three jobs, even when one failed, and fails unless
  all results are `Succeeded`.
- **Inputs:** Dependency results for `appinspect`, `nonprod`, and `prod`.
- **Outputs:** `RESULT: ALL PASS` or `RESULT: FAILED` in the log.

Steps:

- **Checkout self (`checkout: self`):** Gets the smoke-test script.
  **Inputs:** Pipeline repo. **Outputs:** Source checkout.
- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Result:** Prints each job result and checks for three successes.
  **Inputs:** Three dependency results. **Outputs:** Final result line and
  job status.
