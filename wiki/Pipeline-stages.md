# Pipeline stages

[[_TOC_]]

This page follows the checked-in YAML. Steps use their `displayName` when
present. For steps without one, the entry names the YAML action or task.
The shared template defaults to Python 3.13 and checks out the tools repo.
An app repo can override the `setup` and `pool` parameters.

## Main app pipeline

The shared template has a `build` stage on every run and an `appinspect`
stage after it. Pull request runs can continue through `nonprod` and
`proddiff`. Runs from `refs/heads/main` can continue through `release` and,
when the app repo sets `prod: true`, `prod`.

### Stage `build`

- **Does:** Plans the run, sorts and packages the app, and bumps the version
  on a pull request when the target branch has not changed it.
- **Inputs:** App repo, tools repo, Python 3.13, `prod` template parameter,
  build reason and branch variables, `slim`, `ksconf`, and Splunk SDK packages.
- **Outputs:** `dist` pipeline artifact containing the app package.

#### Job `build` in the build stage

- **Does:** Runs on the selected `pool` and prepares the package for later
  stages.
- **Inputs:** App repo; tools repo; `Build.Reason`, `Build.SourceBranch`, and
  `prod`; default `setup` or the app repo override.
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
  **Inputs:** Build reason, source branch, and `prod` parameter.
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

- **Does:** Runs only after a successful AppInspect stage on a pull request.
- **Inputs:** `dist`, `splunk-appinspect` and `splunk-nonprod` groups, and the
  `splunk-nonprod` environment.
- **Outputs:** Nonprod diff artifact and app installation through ACS.

#### Deployment job `deploy` in the nonprod stage

- **Does:** Uses `templates/deploy.yml` to export, compare, and install the
  package in the `splunk-nonprod` environment.
- **Inputs:** `dist`, groups `splunk-appinspect` and `splunk-nonprod`, Python
  setup, `SPLUNK_STACK`, `ACS_TOKEN`, and AppInspect username/password.
- **Outputs:** `nonprod-diff-<attempt>` artifact and installed private app.

Steps from `templates/deploy.yml`, in order:

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
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Export the app from nonprod via ACS:** Exports the configured app.
  **Inputs:** `SPLUNK_STACK` and mapped `ACS_TOKEN` as `STACK_TOKEN`.
  **Outputs:** `nonprod-export/`.
- **Compare nonprod with this package:** Writes local, patch, summary, and
  merged archive reports. **Inputs:** Nonprod export and `dist` package.
  **Outputs:** `nonprod-diff/`.
- **Publish artifact (`nonprod-diff-$(System.JobAttempt)`):** Publishes the
  diff for this attempt. **Inputs:** `nonprod-diff/`. **Outputs:** Attempt-
  named pipeline artifact.
- **Deploy to nonprod via ACS:** Installs the package as a private app.
  **Inputs:** `dist`, `SPLUNK_USERNAME`, `SPLUNK_PASSWORD`, `SPLUNK_STACK`,
  and `ACS_TOKEN` mapped to `STACK_TOKEN`. **Outputs:** App install result.

### Stage `proddiff`

- **Does:** Runs after `nonprod` succeeds on a pull request.
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

### Stage `prod`

- **Does:** Exists only when `prod: true`, and runs after `release` succeeds.
- **Inputs:** `dist`, `splunk-appinspect` and `splunk-prod` groups, and the
  `splunk-prod` environment.
- **Outputs:** `prod-diff-<attempt>` artifact and app installation through
  ACS.

#### Deployment job `deploy` in the prod stage

- **Does:** Uses `templates/deploy.yml` to export, compare, and install the
  package in the `splunk-prod` environment.
- **Inputs:** `dist`, groups `splunk-appinspect` and `splunk-prod`, Python
  setup, `SPLUNK_STACK`, `ACS_TOKEN`, and AppInspect username/password.
- **Outputs:** `prod-diff-<attempt>` artifact and installed private app.

Steps from `templates/deploy.yml`, in order:

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
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Export the app from prod via ACS:** Exports the configured app.
  **Inputs:** `SPLUNK_STACK` and mapped `ACS_TOKEN` as `STACK_TOKEN`.
  **Outputs:** `prod-export/`.
- **Compare prod with this package:** Writes local, patch, summary, and
  merged archive reports. **Inputs:** Prod export and `dist` package.
  **Outputs:** `prod-diff/`.
- **Publish artifact (`prod-diff-$(System.JobAttempt)`):** Publishes the diff
  for this attempt. **Inputs:** `prod-diff/`. **Outputs:** Attempt-named
  pipeline artifact.
- **Deploy to prod via ACS:** Installs the package as a private app.
  **Inputs:** `dist`, `SPLUNK_USERNAME`, `SPLUNK_PASSWORD`, `SPLUNK_STACK`,
  and `ACS_TOKEN` mapped to `STACK_TOKEN`. **Outputs:** App install result.

## Compare pipeline

The manual pipeline accepts target `splunk` or `splunk-itsi` and a space-
separated list of app ids. It exports both environments, then compares prod
as the target against nonprod as the source.

### Job `nonprod` in the compare pipeline

- **Does:** Exports the selected apps from nonprod.
- **Inputs:** Variable group selected for the nonprod target, `SPLUNK_STACK`,
  `SPLUNK_SEARCH_HEAD`, `ACS_TOKEN`, Python 3.13, and app ids.
- **Outputs:** `nonprod-export` artifact.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Install ACS CLI 2.26.0:** Downloads and verifies the CLI.
  **Inputs:** Agent OS, `curl`, release file, checksum. **Outputs:** `acs` on
  `PATH`.
- **ACS CLI version:** Prints the installed version. **Inputs:** `acs` on
  `PATH`. **Outputs:** Version in the log.
- **Export apps from nonprod via ACS:** Exports the requested ids.
  **Inputs:** Nonprod group, `SPLUNK_STACK`, `SPLUNK_SEARCH_HEAD`,
  `ACS_TOKEN`, and `apps`. **Outputs:**
  `$(Pipeline.Workspace)/nonprod-export`.
- **Publish artifact (`nonprod-export`):** Publishes exported files.
  **Inputs:** Nonprod export directory. **Outputs:** `nonprod-export` artifact.

### Job `prod` in the compare pipeline

- **Does:** Exports the selected apps from prod.
- **Inputs:** Variable group selected for the prod target, `SPLUNK_STACK`,
  `SPLUNK_SEARCH_HEAD`, `ACS_TOKEN`, Python 3.13, and app ids.
- **Outputs:** `prod-export` artifact.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Install ACS CLI 2.26.0:** Downloads and verifies the CLI.
  **Inputs:** Agent OS, `curl`, release file, checksum. **Outputs:** `acs` on
  `PATH`.
- **ACS CLI version:** Prints the installed version. **Inputs:** `acs` on
  `PATH`. **Outputs:** Version in the log.
- **Export apps from prod via ACS:** Exports the requested ids.
  **Inputs:** Prod group, `SPLUNK_STACK`, `SPLUNK_SEARCH_HEAD`,
  `ACS_TOKEN`, and `apps`. **Outputs:**
  `$(Pipeline.Workspace)/prod-export`.
- **Publish artifact (`prod-export`):** Publishes exported files.
  **Inputs:** Prod export directory. **Outputs:** `prod-export` artifact.

### Job `compare` in the compare pipeline

- **Does:** Waits for both export jobs and compares prod to nonprod.
- **Inputs:** `prod-export`, `nonprod-export`, Python 3.13, `ksconf`, and
  Splunk SDK.
- **Outputs:** `compare` artifact.

Steps:

- **UsePythonVersion@0:** Selects Python 3.13. **Inputs:** `versionSpec`.
  **Outputs:** Python on `PATH`.
- **Download artifacts (`download: current`):** Gets current-run exports.
  **Inputs:** Published artifacts. **Outputs:** Export directories.
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Compare prod with nonprod:** Writes per-app reports.
  **Inputs:** Prod target and nonprod source exports. **Outputs:**
  `$(Pipeline.Workspace)/compare`.
- **Publish artifact (`compare`):** Publishes the reports.
  **Inputs:** Compare directory. **Outputs:** `compare` artifact.

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
