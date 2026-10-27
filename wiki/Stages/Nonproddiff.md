# Nonproddiff stage

This page lists the nonprod comparison stage inputs, jobs, and reports.

## Stage `nonproddiff`

- **Display name:** `Compare with nonprod`.
- **Does:** Runs after AppInspect on pull requests and `main` runs.
- **Inputs:** The `dist` package, `splunk-nonprod`, and
  `splunk-itsi-nonprod` variable groups.
- **Outputs:** `nonprod-diff-<app-id>-<attempt>` and
  `itsi-nonprod-diff-<app-id>-<attempt>` artifacts.

### Jobs `compare_nonprod` and `compare_itsi_nonprod`

The jobs run in parallel. Each job compares the package with one search head
and installs nothing.

- **`compare_nonprod`:** Displays as **Compare with nonprod** and uses
  `splunk-nonprod`.
- **`compare_itsi_nonprod`:** Displays as **Compare with itsi-nonprod** and
  uses `splunk-itsi-nonprod`.

Each job runs the package steps, installs diff tools, sets up the ACS CLI,
then checks stack status and exports the installed app. It runs four compare
steps:

- **Compare `<side>` with this package (file tree, local and default):** Writes
  the file tree report.
- **Compare `<side>` with this package (local files vs default):** Writes the
  local-versus-default report.
- **Compare `<side>` with this package (merged defaults):** Writes the patch,
  summary, HTML report, and merged archive.
- **Compare `<side>` with this package (data models):** Writes the data model
  patch.

Each job publishes `<side>-diff-<app-id>-<attempt>` with its reports.
