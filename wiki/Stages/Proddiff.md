# Proddiff stage

This page lists the production comparison stage inputs, jobs, and reports.

## Stage `proddiff`

- **Display name:** `Compare with prod`.
- **Does:** Runs after `nonprod` on pull requests and `main` runs.
- **Inputs:** The `dist` package, `splunk-prod`, and `splunk-itsi-prod`
  variable groups.
- **Outputs:** `prod-diff-<app-id>-<attempt>` and
  `itsi-prod-diff-<app-id>-<attempt>` artifacts.

### Jobs `compare_prod` and `compare_itsi_prod`

- **Does:** Each job compares the package with one production search head.
  They run in parallel and install nothing.
- **Inputs:** `splunk-prod` or `splunk-itsi-prod`, the `dist` package, and
  Python setup.
- **Outputs:** `prod-diff-<app-id>-<attempt>` or
  `itsi-prod-diff-<app-id>-<attempt>` pipeline artifact.

The jobs display as **Compare with prod** and **Compare with itsi-prod**. They
do not install the package. Each job runs the package steps, installs diff
tools, sets up the ACS CLI, then checks stack status and exports the installed
app. It runs four compare steps:

- **Compare `<side>` with this package (file tree, local and default):** Writes
  the file tree report.
- **Compare `<side>` with this package (local files vs default):** Writes the
  local-versus-default report.
- **Compare `<side>` with this package (merged defaults):** Writes the patch,
  summary, HTML report, and merged archive.
- **Compare `<side>` with this package (data models):** Writes the data model
  patch.

Each job publishes `<side>-diff-<app-id>-<attempt>` with its reports.
