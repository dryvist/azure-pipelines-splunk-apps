# Manual deploy setup

Create and run the manual app deployment pipeline.

## Step 12: Create the manual app deployment pipeline

| Pipeline name | YAML path |
| --- | --- |
| `deploy-apps` | `/deploy/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

1. Select **Run pipeline**.
2. Select `nonprod` or `prod` for `environment`.
3. Enter app IDs separated by spaces for `apps`.
4. Select **Run**.
5. Permit each requested variable group and environment using [Permissions troubleshooting](/Troubleshooting/Permissions).
6. Rerun the pipeline if resource authorization stopped the run.
7. Complete any approval check on the selected environment.

**Verify:**

1. Confirm the pipeline uses the selected `splunk-<environment>` group.
2. Confirm the deployment uses the matching `splunk-<environment>` approval.
3. Confirm the run shows one **Compare** stage per app and one **Install apps** stage.

For stage order, see [Deploy pipeline](/Pipelines/Deploy-pipeline).

If a run fails, use [Deploy troubleshooting](/Troubleshooting/Deploy).
