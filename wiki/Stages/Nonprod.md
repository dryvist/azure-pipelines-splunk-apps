# Nonprod stage

[Home](/Home) > [Stages](/Stages) > Nonprod stage

[[_TOC_]]

## Stage `nonprod`

- **Display name:** `Deploy to nonprod`.
- **Does:** Runs after `nonproddiff` on pull requests and `main` runs.
- **Inputs:** The `dist` package, groups `splunk-appinspect` and
  `splunk-nonprod`, and the `splunk-nonprod` environment.
- **Outputs:** App installation through ACS.
- **Lock:** Uses sequential lock behavior.

### Deployment job `deploy`

- **Display name:** `Install on nonprod`.
- **Does:** Sets up the ACS CLI, then installs the package. It does not
  compare the package with nonprod.
- **Inputs:** Package steps, the AppInspect and nonprod groups, Python setup,
  `SPLUNK_STACK`, and `ACS_TOKEN`.
- **Outputs:** App install result and confirmed package version.

The job checks stack status before and after deployment. The shared deploy
template can uninstall the app before installation when enabled.

## Related

- [Nonproddiff stage](/Stages/Nonproddiff)
- [Deploy pipeline](/Pipelines/Deploy-pipeline)
- [Troubleshooting](/Troubleshooting/Nonprod)

---

[< Previous: Nonproddiff stage](/Stages/Nonproddiff) |
[Next: Proddiff stage >](/Stages/Proddiff)
