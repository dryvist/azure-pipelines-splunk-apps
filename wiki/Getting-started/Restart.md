# Restart pipeline setup

[Home](/Home) > [Getting started](/Getting-started) > Restart pipeline setup

[[_TOC_]]

Step 15 creates the restart pipeline.

## Step 15: Create the restart pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/restart/azure-pipelines.yml`.
4. Enter `restart-stack` as the pipeline name.
5. Save the pipeline.
6. Select **Edit**.
7. Select **⋮** (More actions) at the top right.
8. Select **Triggers**.
9. Select the **YAML** tab.
10. In **Default agent pool for YAML**, select an agent pool.
11. Select the arrow next to **Save & queue**.
12. Select **Save**.
13. Select **Run pipeline**.
14. Select `nonprod` or `prod` for `environment`.
15. Select `splunk` or `splunk-itsi` for `target`.
16. Select **Run**.
17. When asked, permit the selected variable group.

**Verify:**

1. Confirm the restart job completes.
2. Confirm the final stack status does not report a required restart.

## Related

- [Restart pipeline](/Pipelines/Restart-pipeline)

---

[< Previous: Compare pipeline setup](/Getting-started/Compare)
