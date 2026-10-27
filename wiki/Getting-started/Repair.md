# Repair pipeline setup

Configure the REST API access and create the repair pipeline.

## Step 19: Allow the agent on the REST API

**Where:** Splunk Web of the nonprod stack, **Settings → Server settings → IP
allow list**

**Do:**

1. Select **Search head API access**.
2. Add the agent's public IP address.
3. Select **Save**.
4. Repeat steps 1 to 3 in Splunk Web of the prod stack.

**Verify:** Both stacks list the agent's address under **Search head API
access**.

## Step 20: Add the REST URL for search head groups

**Where:** **Pipelines → Library**

**Do:**

1. Open the `splunk-itsi-nonprod` variable group.
2. Add a variable.
3. Type `SPLUNK_REST_URL` as the variable name.
4. Type the nonprod ITSI search head REST URL, such as
   `https://<host>.splunkcloud.com:8089`.
5. Set its lock icon off.
6. Select **Save**.
7. Open the `splunk-itsi-prod` variable group.
8. Repeat steps 2 to 6 with the prod ITSI search head REST URL.
9. Repeat steps 2 to 6 for any other group that sets `SPLUNK_SEARCH_HEAD`.

**Verify:** Each group with `SPLUNK_SEARCH_HEAD` also has `SPLUNK_REST_URL`.

## Step 21: Create the repair pipeline

| Pipeline name | YAML path |
| --- | --- |
| `repair-app-objects` | `/repair/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

**Verify:** The pipeline appears under **Pipelines** with no runs.

For run inputs and order, see [Repair pipeline](/Pipelines/Repair-pipeline).

If a REST request fails, follow [Troubleshooting permissions](/Troubleshooting/Permissions).
