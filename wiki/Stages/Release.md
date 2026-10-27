# Release stage

This page lists the release stage inputs, outputs, and steps.

## Stage `release`

- **Does:** Runs after Proddiff on `refs/heads/main`.
- **Inputs:** `dist`, app repo checkout, repository credentials, and the
  `splunk-apps` package feed.
- **Outputs:** Version tag and Universal Package in the feed.

### Job `release` in the release stage

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
- **Use UTF-8 for Python files and output (default `setup`):** Sets
  `PYTHONUTF8=1` for later steps.
- **Download artifact (`download: current`, `dist`):** Gets the package.
  **Inputs:** `dist` artifact. **Outputs:** `dist/` in the workspace.
- **Tag the release version:** Creates and pushes `v<version>`; sets
  `APP_ID` and `APP_VERSION`. When the feed already holds that version, prints
  `<app-id> <version> is already in the splunk-apps feed, skipping publish`
  and sets `PACKAGE_PUBLISHED`. **Inputs:** App version, repo credentials and
  `System.AccessToken`. **Outputs:** Git tag and pipeline variables.
- **Publish the package to the splunk-apps feed (`UniversalPackages@0`):**
  Publishes the package. Skipped when `PACKAGE_PUBLISHED` is `true`.
  **Inputs:** `dist/`, `APP_ID`, `APP_VERSION`, and feed permissions.
  **Outputs:** Universal Package in the feed.
