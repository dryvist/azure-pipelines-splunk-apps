# Repair pipeline setup

[Home](/Home) > [Getting started](/Getting-started) > Repair pipeline setup

[[_TOC_]]

Steps 19 to 21 give the repair pipeline REST API access and create it.

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

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/repair/azure-pipelines.yml`.
4. Enter `repair-app-objects` as the pipeline name.
5. Save the pipeline.
6. Select **Edit**.
7. Select **⋮** (More actions) at the top right.
8. Select **Triggers**.
9. Select the **YAML** tab.
10. In **Default agent pool for YAML**, select an agent pool.
11. Select the arrow next to **Save & queue**.
12. Select **Save**.

**Verify:** The pipeline appears under **Pipelines** with no runs.

## Related

- [Repair pipeline](/Pipelines/Repair-pipeline)

---

[< Previous: Bulk pipelines](/Getting-started/Bulk-pipelines)
