# Nonprod stage

[Home](/Home) > [Stages](/Stages) > Nonprod stage

[[_TOC_]]

## Stage `nonprod`

The `nonprod` and `prod` stages share `templates/deploy-stage.yml`. The
template sets `lockBehavior: sequential`.

- **Does:** Runs after a successful AppInspect stage on a pull request or
  `refs/heads/main` run.
- **Inputs:** `dist`, `splunk-appinspect` and `splunk-nonprod` groups, and the
  `splunk-nonprod` environment.
- **Outputs:** Nonprod diff artifact and app installation through ACS.

### Deployment job `deploy` in the nonprod stage

- **Does:** Uses `templates/deploy.yml` to export, compare, and install the
  package in the `splunk-nonprod` environment.
- **Inputs:** `dist`, groups `splunk-appinspect` and `splunk-nonprod`, Python
  setup, `SPLUNK_STACK`, `ACS_TOKEN`, and AppInspect username/password.
- **Outputs:** `nonprod-diff-<app>-<attempt>` artifact and installed private
app.

The deployment job selects Python 3.13, installs diff dependencies once,
downloads `dist`, and includes shared ACS setup before package steps. See
[release.py commands](/Reference/Release.py-commands) for the ACS setup
lifecycle. `templates/deploy.yml` runs these steps for the package:

- **Check stack status before deploy:** Reports status and warns if restart
  is required. **Inputs:** Nonprod ACS session.
- **Export this app from nonprod via ACS:** Gets the app id from the package
  filename and exports the installed app.
  **Inputs:** `SPLUNK_STACK` and `ACS_TOKEN`.
  **Outputs:** `nonprod-export/`.
- **Compare nonprod with this package (file tree, local and default):** Writes
  `<app-id>-tree.txt` with raw file changes.
- **Compare nonprod with this package (local files vs default):** Writes the
  local-versus-default report. **Inputs:** Nonprod export and `dist` package.
- **Compare nonprod with this package (merged defaults):** Writes the patch,
  summary, HTML report, and merged archive. **Inputs:** Nonprod export and
  `dist` package. **Outputs:** `nonprod-diff/`.
- **Compare nonprod with this package (data models):** Prints each changed
  data model JSON file in its own collapsed group, one key per line, and
  writes `<app-id>-data-models.patch`. **Inputs:** Nonprod export and `dist`
  package. **Outputs:** `nonprod-diff/`.
- **Publish artifact (`nonprod-diff-<app>-$(System.JobAttempt)`):** Publishes
  this app's diff. **Inputs:** App diff directory. **Outputs:** Attempt-named
  pipeline artifact.
- **Deploy to nonprod via ACS:** Installs the package as a private app.
  **Inputs:** `dist`, `SPLUNK_USERNAME`, `SPLUNK_PASSWORD`, `SPLUNK_STACK`,
  and `ACS_TOKEN`. **Outputs:** App install result.
- **Wait for the deployed version:** Checks `acs apps describe` every 15
  seconds for up to 15 minutes. **Inputs:** Package version and ACS session.
  **Outputs:** Confirmed app version or a timeout error.
- **Check stack status after deploy:** Prints current stack status and warns
  if a restart is required. **Inputs:** Nonprod ACS session.

## Related

- [Deploy pipeline](/Pipelines/Deploy-pipeline)
- [Troubleshooting](/Troubleshooting/Nonprod)

---

[< Previous: AppInspect stage](/Stages/AppInspect) |
[Next: Proddiff stage >](/Stages/Proddiff)
