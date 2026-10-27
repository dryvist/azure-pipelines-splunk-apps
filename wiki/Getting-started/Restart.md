# Restart pipeline setup

Create and run the stack restart pipeline.

## Step 15: Create the restart pipeline

| Pipeline name | YAML path |
| --- | --- |
| `restart-stack` | `/restart/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

1. Select **Run pipeline**.
2. Select `nonprod` or `prod` for `environment`.
3. Select `splunk` or `splunk-itsi` for `target`.
4. Select **Run**.
5. Permit the requested variable group using [Permissions troubleshooting](/Troubleshooting/Permissions).

**Verify:**

1. Confirm the restart job completes.
2. Confirm the final stack status does not report a required restart.

For job behavior, see [Restart pipeline](/Pipelines/Restart-pipeline).

If the run fails, use [Nonprod troubleshooting](/Troubleshooting/Nonprod).
