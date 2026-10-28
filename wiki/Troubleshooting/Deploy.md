# Deploy troubleshooting

Use this page to fix deploy failures, waits, and version checks.

## An app does not start deploying

**Symptom:** A selected app does not start deploying, or its job waits.

**Fix:**

1. Confirm **App IDs** contains the package IDs, separated by `;`.
2. Confirm each package is published in `splunk-apps`.
3. Permit the selected variable group and deployment environment. See
   [Permissions](/Troubleshooting/Permissions).
4. Complete any approval check on the selected environment.

## `<app-id> is not in the splunk-apps feed`

**Symptom:** The **Check `<app-id>` is in the splunk-apps feed** step fails. The `release_missing` stage did not
upload the app.

**Fix:**

1. Open the `release_missing` stage and find the app's failed job.
2. For **Package `<app-id>` and run AppInspect**, open the `appinspect-report-<app-id>-<attempt>` artifact and fix
   the failures on `main`.
3. For **Upload `<app-id>` to the splunk-apps feed**, grant the Build Service rights in
   [Build Service: App repository](/Setup/Build-service#app-repository).
4. Start a new deploy run with the app ID.

## `ACS is busy with another deployment task`

**Symptom:** A step prints `ACS is busy with another deployment task, retrying in 30 seconds`. ACS returns
`424-failed-dependency` or `503-service-unavailable` until another install, uninstall, or configuration change
finishes.

**Fix:**

1. Wait. The step retries for up to 15 minutes.
2. If the step fails after 15 minutes, check the stack for a stuck task.
3. Rerun the failed job.

## A deploy stage waits for the environment lock

**Symptom:** An uninstall, install, or restart stage waits while another run uses the same environment. The
**Exclusive Lock** check allows one deployment job at a time.

**Fix:**

1. Wait for the active deployment job to finish.
2. If it does not finish, inspect that run and resolve its failed or pending step.
3. Confirm the **Exclusive Lock** check is set up. See [Environments and ACS](/Setup/Environments-and-ACS).

## `Restart required on <stack>`

**Symptom:** A deploy job prints `Restart required on <stack>` in its status step. The step warns and
continues. It does not restart the stack.

**Fix:**

1. Open the [Restart pipeline](/Pipelines/Restart).
2. Select the same environment as the deploy job.
3. Select `splunk` for **target**.
4. Run the pipeline. Confirm the final status has no restart requirement.

## The installed version check times out

**Symptom:** **Check the installed version** reports a timeout after 15 minutes.

**Fix:**

1. Confirm the deploy step succeeded.
2. Compare the package filename version with the version ACS reports for the app.
3. Rerun the deployment after the app reports the expected version.

For stage order, see [Deploy pipeline](/Pipelines/Deploy). For log details, see
[Reading logs](/Troubleshooting/Reading-logs).
