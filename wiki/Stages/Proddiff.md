# Proddiff stage

[Home](/Home) > [Stages](/Stages) > Proddiff stage

[[_TOC_]]

## Stage `proddiff`

- **Does:** Runs after `nonprod` succeeds on a pull request or
  `refs/heads/main` run.
- **Inputs:** `dist`, `splunk-prod`, tools repo, and Python setup.
- **Outputs:** `prod-diff-<attempt>` artifact for review.

### Job `proddiff` in the proddiff stage

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
- **Set up ACS CLI 2.26.0 for $(SPLUNK_STACK):** Prepares the ACS CLI
  session before export. **Inputs:** Agent OS, `curl`, checksum,
  `SPLUNK_STACK`, and `ACS_TOKEN`. **Outputs:** `acs` on `PATH` and its
  configuration for later steps. See the
  [ACS setup lifecycle](/Reference/Release.py-commands).
- **Export the app from production via ACS:** Exports the configured app.
  **Inputs:** `SPLUNK_STACK` and `ACS_TOKEN`.
  **Outputs:** `prod-export/`.
- **Install diff dependencies:** Installs `ksconf` and Splunk SDK.
  **Inputs:** Python package index. **Outputs:** Diff tools in Python.
- **Diff production against this package (local files vs default):** Runs
  `release.py local-diff`. **Inputs:** `prod-export/` and `dist/`.
  **Outputs:** Local-versus-default reports in `prod-diff/`.
- **Diff production against this package (merged defaults):** Runs
  `release.py diff`. **Inputs:** `prod-export/` and `dist/`.
  **Outputs:** Patch, summary, HTML, and merged archive reports in
  `prod-diff/`.
- **Publish artifact (`prod-diff-$(System.JobAttempt)`):** Publishes this
  attempt's reports. **Inputs:** `prod-diff/`. **Outputs:** Attempt-named
  pipeline artifact.

## Related

- [Nonprod stage](/Stages/Nonprod)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Nonprod stage](/Stages/Nonprod) |
[Next: Release stage >](/Stages/Release)
