# Proddiff stage

[Home](/Home) > [Stages](/Stages) > Proddiff stage

[[_TOC_]]

## Stage `proddiff`

- **Does:** Runs after `nonprod` succeeds on a pull request or
  `refs/heads/main` run.
- **Inputs:** `dist`, `splunk-prod`, `splunk-itsi-prod`, tools repo, and
  Python setup.
- **Outputs:** `prod-diff-<attempt>` and `itsi-prod-diff-<attempt>` artifacts
  for review.

### Jobs `proddiff_prod` and `proddiff_itsi_prod` in the proddiff stage

- **Does:** Each job exports the app from one prod search head and compares it
  with the package. `<side>` is `prod` for the search head that installs
  replace (group `splunk-prod`) and `itsi-prod` for the prod ITSI search head
  (group `splunk-itsi-prod`). The two jobs run in parallel.
- **Inputs:** `splunk-<side>` group, `SPLUNK_STACK`, `SPLUNK_SEARCH_HEAD`,
  `ACS_TOKEN`, `dist`, and Python 3.13.
- **Outputs:** `<side>-diff-<attempt>` pipeline artifact.

Steps, in order:

- **Checkout app (`checkout: self`):** Gets the app repo at `app`.
  **Inputs:** App repo revision. **Outputs:** App checkout.
- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Use UTF-8 for Python files and output (default `setup`):** Sets
  `PYTHONUTF8=1` for later steps.
- **Download artifact (`download: current`, `dist`):** Gets the package.
  **Inputs:** `dist` artifact. **Outputs:** `dist/` in the workspace.
- **Set up ACS CLI 2.26.0 for $(SPLUNK_STACK):** Prepares the ACS CLI
  session before export. **Inputs:** Agent OS, `curl`, checksum,
  `SPLUNK_STACK`, and `ACS_TOKEN`. **Outputs:** `acs` on `PATH` and its
  configuration for later steps. See the
  [ACS setup lifecycle](/Reference/Release.py-commands).
- **Export the app from `<side>` via ACS:** Exports the configured app.
  **Inputs:** `SPLUNK_STACK` and `ACS_TOKEN`.
  **Outputs:** `<side>-export/`.
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Compare `<side>` against this package (file tree, local and
  default):** Runs `release.py tree`. **Inputs:** `<side>-export/` and `dist/`.
  **Outputs:** `<app-id>-tree.txt` in `<side>-diff/`.
- **Compare `<side>` against this package (local files vs default):** Runs
  `release.py local-diff`. **Inputs:** `<side>-export/` and `dist/`.
  **Outputs:** Local-versus-default reports in `<side>-diff/`.
- **Compare `<side>` against this package (merged defaults):** Runs
  `release.py diff`. **Inputs:** `<side>-export/` and `dist/`.
  **Outputs:** Patch, summary, HTML, and merged archive reports in
  `<side>-diff/`.
- **Compare `<side>` against this package (data models):** Runs
  `release.py data-models`. **Inputs:** `<side>-export/` and `dist/`.
  **Outputs:** `<app-id>-data-models.patch` in `<side>-diff/`.
- **Publish artifact (`<side>-diff-$(System.JobAttempt)`):** Publishes this
  attempt's reports. **Inputs:** `<side>-diff/`. **Outputs:** Attempt-named
  pipeline artifact.

## Related

- [Nonprod stage](/Stages/Nonprod)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Nonprod stage](/Stages/Nonprod) |
[Next: Release stage >](/Stages/Release)
