# Restart pipeline

The restart pipeline restarts a stack when ACS reports that the stack needs a restart.

The pipeline is named `restart-stack` in [Manual pipelines](/Setup/Manual-pipelines).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to restart. |
| `target` | `splunk`, `splunk-itsi` | `splunk` | `splunk` uses `splunk-<environment>`. `splunk-itsi` uses `splunk-itsi-<environment>`. |

ACS commands pass `SPLUNK_SEARCH_HEAD` when the group sets it.

## Run it

1. Open the restart pipeline and select **Run pipeline**.
2. Select `nonprod` or `prod` for **environment**.
3. Select `splunk` or `splunk-itsi` for **target**.
4. Select **Run**.
5. Permit the requested variable group. See [Permissions](/Troubleshooting/Permissions).

Verify that the restart job completes. The final stack status must not report a required restart.

## What happens

One job runs, named **Restart `<target>-<environment>` if required**. It uses a clean workspace, Python 3.13,
the ACS CLI setup for the stack, and the selected variable group. Its steps run in this order:

1. **Check stack status before restart** reads whether a restart is required.
2. **Restart the current stack** runs only when the status reports `restartRequired: true`. It then waits up
   to 30 minutes for the flag to clear.
3. **Check stack status after restart** reads the status again.

![Restart pipeline flow.](../diagrams/restart-pipeline.png)

If the run fails, see [ACS troubleshooting](/Troubleshooting/ACS).
