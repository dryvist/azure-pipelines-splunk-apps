# Deploy troubleshooting

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Deploy troubleshooting

[[_TOC_]]

## Manual deploy pipeline

**Symptom:** A selected app does not start deploying or the job waits.

**Cause:** The pipeline cannot access the selected feed package, variable
group, deployment environment, or its approval checks.

**Fix:**

1. Confirm `apps` contains feed package ids separated by spaces.
2. Confirm each package exists in `splunk-apps`.
3. Permit the selected `splunk-<environment>` group and environment.
4. Complete any approval check on the selected environment.

Each app has its own compare and deploy stage. When **Restart** is checked,
the restart stage runs once, only after every deploy stage succeeds.

### ACS is busy

**Symptom:** A step prints `ACS is busy with another deployment task, retrying
in 30 seconds`.

**Cause:** Another install, uninstall, or configuration change is running on
the stack. ACS returns `424-failed-dependency` or `503-service-unavailable`
until it finishes.

**Fix:**

1. Wait. The step retries for up to 15 minutes.
2. If the step fails after 15 minutes, check the stack for a stuck task.
3. Rerun the failed job.

### App is not in the splunk-apps feed

**Symptom:** **Check `<app-id>` is in the splunk-apps feed** fails with
`<app-id> is not in the splunk-apps feed`.

**Cause:** The app pipeline has not finished a **Release** stage on `main`.

**Fix:**

1. Select **Pipelines**.
2. Open the app's pipeline.
3. Select **Run pipeline**.
4. Select the `main` branch.
5. Select **Run**.
6. Wait for the **Release** stage to finish.
7. Start a new deploy run with the app id.

### Two apps install at the same time

**Symptom:** Two **Deploy** stages run at once.

**Cause:** The `splunk-<environment>` environment has no **Exclusive Lock**
check.

**Fix:**

1. Add the check with [Step 3](/Getting-started/Environments-and-ACS).
2. Rerun the pipeline.

**Docs:** [Deploy pipeline](/Pipelines/Deploy-pipeline),
[variable groups](/Reference/Variable-groups),
[environments](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments),
[approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals).

## Deployment status and version wait

### Deployment reports that a restart is required

**Symptom:** A deploy job prints `Restart required on <stack>` in its status
step.

**Cause:** `acs status current-stack` reports that a restart is required. The
status step warns and continues; it does not restart the stack.

**Fix:**

1. Run the restart pipeline.
2. Select the same environment used by the deploy job.
3. Select `splunk` for the restart pipeline target.
4. Confirm the restart job completes and the final status has no restart
   requirement.

**Docs:** [Restart pipeline](/Pipelines/Restart-pipeline),
[Deploy pipeline](/Pipelines/Deploy-pipeline),
[ACS CLI](https://github.com/splunk/acs-cli).

### Version wait times out

**Symptom:** `Check the installed version` reports a timeout after 300
seconds.

**Cause:** `acs apps describe` did not report the version in the package name
before the wait deadline.

**Fix:**

1. Confirm the deploy step succeeded.
2. Compare the package filename version with the version ACS reports for the
   app.
3. Rerun the deployment after the app reports the expected version.

**Docs:** [Deploy pipeline](/Pipelines/Deploy-pipeline),
[ACS CLI](https://github.com/splunk/acs-cli).

## Related

- [Deploy pipeline](/Pipelines/Deploy-pipeline)
- [Restart pipeline](/Pipelines/Restart-pipeline)

---

[< Previous: Release troubleshooting](/Troubleshooting/Release) |
[Next: Compare troubleshooting >](/Troubleshooting/Compare)
