# AppInspect stage

[Home](/Home) > [Stages](/Stages) > AppInspect stage

[[_TOC_]]

## Stage `appinspect`

- **Does:** Runs after `build`; only a passing result allows later stages.
- **Inputs:** `dist`, Python 3.13, `splunk-appinspect`, AppInspect credentials,
  and the AppInspect service.
- **Outputs:** AppInspect result and `appinspect-report-<attempt>` artifact.

### Job `appinspect` in the appinspect stage

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
  `future_failure` checks. The log prints the summary in two sections:
  **Blocks deployment** (`status`, `error`, `failure`, `manual_check`) and
  **Does not block deployment** (every other count).
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

## Related

- [Build stage](/Stages/Build)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Build stage](/Stages/Build) |
[Next: Nonprod stage >](/Stages/Nonprod)
