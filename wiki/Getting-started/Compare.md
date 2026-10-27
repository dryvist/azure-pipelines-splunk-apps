# Compare pipeline setup

Use these settings to create and run the compare pipeline.

| Pipeline name | YAML path |
| --- | --- |
| `compare-environments` | `/compare/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

1. Select **Run pipeline**.
2. Select `splunk` or `splunk-itsi` for `groupPrefix`.
3. Select `nonprod` or `prod` for `source`.
4. Select `nonprod` or `prod` for `target`.
5. Leave `apps` as `all` or empty to compare all custom apps. To select apps, enter their IDs separated by `;`.
   Use the app folder names from `[id] name`, not display labels. For example: `my_app;other_app`.
6. Select **Run**.
7. Permit the selected source variable group.
8. Permit the selected target variable group.

**Verify:** The `source`, `target`, and `compare` jobs succeed. The `compare` artifact holds the reports for each app.

For report names and contents, see [Artifacts](/Reference/Artifacts). For compare behavior, see [Compare pipeline](/Pipelines/Compare-pipeline).

If a run fails, use [Compare troubleshooting](/Troubleshooting/Compare).
