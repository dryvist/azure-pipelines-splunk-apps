# Manual deploy setup

[Home](/Home) > [Getting started](/Getting-started) > Manual deploy setup

[[_TOC_]]

Step 12 creates the manual app deployment pipeline.

## Step 12: Create the manual app deployment pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/deploy/azure-pipelines.yml`.
4. Enter `deploy-apps` as the pipeline name.
5. Save the pipeline.
6. Select **Run pipeline**.
7. Select `nonprod` or `prod` for `environment`.
8. Enter app ids separated by spaces for `apps`.
9. Select **Run**.
10. Permit the `splunk-appinspect` variable group if asked.
11. Permit the selected `splunk-<environment>` variable group if asked.
12. Permit the selected `splunk-<environment>` deployment environment if asked.
13. Rerun the pipeline if resource authorization stopped the run.
14. Complete any approval check on the selected environment.

**Verify:**

1. Confirm the pipeline uses the selected `splunk-<environment>` group.
2. Confirm the deployment uses the matching `splunk-<environment>` approval.
3. Confirm the run shows a **Compare** stage for each app id and one **Install
   apps on `<environment>`** stage.
4. Confirm the compare artifact name includes the environment, app id, and
   attempt.
5. Confirm the **Restart** stage starts after the **Install apps** stage
   finishes.

## Related

- [Deploy pipeline](/Pipelines/Deploy-pipeline)

---

[< Previous: Release setup](/Getting-started/Release) |
[Next: Publish the wiki >](/Getting-started/Publish-wiki)
