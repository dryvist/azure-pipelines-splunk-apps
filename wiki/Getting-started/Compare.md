# Compare pipeline setup

[Home](/Home) > [Getting started](/Getting-started) > Compare pipeline setup

[[_TOC_]]

Step 14 creates the compare pipeline.

## Step 14: Create the compare pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/compare/azure-pipelines.yml`.
4. Enter `compare-environments` as the pipeline name.
5. Save the pipeline.
6. Select **Edit**.
7. Select **⋮** (More actions) at the top right.
8. Select **Triggers**.
9. Select the **YAML** tab.
10. In **Default agent pool for YAML**, select your agent pool.
11. Select the arrow next to **Save & queue**.
12. Select **Save**.
13. Select **Run pipeline**.
14. Select `splunk` or `splunk-itsi` for `groupPrefix` in the Run panel.
15. Select `nonprod` or `prod` for `source`.
16. Select `nonprod` or `prod` for `target`.
17. Leave **App IDs, separated by spaces** empty to export every custom app,
    or enter app ids such as `my_app other_app`. Use app folder names from
    `[id] name`, not display labels.
18. Select **Run**.
19. When asked, permit the selected source variable group.
20. When asked, permit the selected target variable group.

**Verify:**

1. Confirm the `source` job succeeds.
2. Confirm the `target` job succeeds.
3. Confirm the `compare` job succeeds.
4. Confirm the `compare` artifact holds `<app-id>-tree.txt`,
   `<app-id>-diff.html`, and `<app-id>-local-vs-default.diff` for each app.
5. Confirm the `compare` artifact holds `<app-id>-summary.md` for each app.
6. Confirm each summary appears on the run summary tab.

## Related

- [Compare pipeline](/Pipelines/Compare-pipeline)

---

[< Previous: Publish the wiki](/Getting-started/Publish-wiki) |
[Next: Restart pipeline setup >](/Getting-started/Restart)
