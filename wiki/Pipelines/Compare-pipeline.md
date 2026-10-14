# Compare pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Compare pipeline

[[_TOC_]]

## Inputs and jobs

The manual pipeline selects `source` and `target` environments independently, each
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

![Compare any two environments.](../diagrams/compare-any-environments.png)

## Related

- [Variable groups](/Reference/Variable-groups)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Deploy pipeline](/Pipelines/Deploy-pipeline) |
[Next: Restart pipeline >](/Pipelines/Restart-pipeline)
