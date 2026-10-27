# Manual pipelines

One time. Done at project setup; you should not need this again.

Create each manual pipeline from its name and YAML path.

| Pipeline name | YAML path | Page |
| --- | --- | --- |
| `deploy-apps` | `/deploy/azure-pipelines.yml` | [Deploy](/Pipelines/Deploy) |
| `compare-environments` | `/compare/azure-pipelines.yml` | [Compare](/Pipelines/Compare) |
| `restart-stack` | `/restart/azure-pipelines.yml` | [Restart](/Pipelines/Restart) |
| `repair-app-objects` | `/repair/azure-pipelines.yml` | [Repair](/Pipelines/Repair) |
| `smoke-test` | `/smoke-test/azure-pipelines.yml` | [Smoke test](/Pipelines/Smoke-test) |
| `Splunk ACS Bulk Install` | `/bulk-install/azure-pipelines.yml` | [Bulk install](/Pipelines/Bulk-Install) |
| `Splunk ACS Bulk Update` | `/bulk-update/azure-pipelines.yml` | [Bulk update](/Pipelines/Bulk-Update) |
| `Splunk ACS Bulk Delete` | `/bulk-delete/azure-pipelines.yml` | [Bulk delete](/Pipelines/Bulk-Delete) |
| Any name you choose | `/onboard/azure-pipelines.yml` | [Onboard](/Pipelines/Onboard) |

Follow these steps for each row.

1. Open **Pipelines**. Select **New pipeline**, then **Azure Repos Git**.
2. Select the repository that contains the YAML file.
3. Select **Existing Azure Pipelines YAML file**.
4. Select branch `main`, then select the YAML path from the table.
5. Select **Continue**.
6. Enter the pipeline name from the table.
7. Select the arrow next to **Save & run**, then select **Save**.
8. Select **Edit**. Select **⋮** (More actions), then **Triggers**.
9. Select the **YAML** tab. Select **Default agent pool for YAML**, then choose the configured pool.
10. Select the arrow next to **Save & queue**, then select **Save**.
11. Confirm the pipeline appears under **Pipelines** with no runs.

If resource access fails, see [Permissions](/Troubleshooting/Permissions).
