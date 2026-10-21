# Deploy to production

[Home](/Home) > [Pipelines](/Pipelines) > Deploy to production

[[_TOC_]]

Deploy a set of apps to prod, reviewing each app's compare with prod before
you approve its install. Nothing installs until you approve that app.

## Before you start

**Do:**

1. On the workstation, open the folder of the `azure-pipelines-splunk-apps`
   repository.
2. Run `git sync`.
3. Select **Pipelines → Environments**.
4. Open `splunk-prod`.
5. Select **Approvals and checks**.
6. Confirm the list shows **Approvals** and **Exclusive Lock**. If either is
   missing, add it with
   [Step 3](/Getting-started/Environments-and-ACS).
7. Confirm the **Approvals** check has a **Timeout** of `24 hours`.

**Verify:**

1. `splunk-prod` has an approval check.
2. `splunk-prod` has an exclusive lock check, so one app installs at a time.
3. The **Approvals** check has a **Timeout** of `24 hours`.

## Release each app

Repeat for every app you plan to deploy.

**Do:**

1. Select **Pipelines**.
2. Open the app's pipeline.
3. Open the latest run on `main`.
4. Confirm every stage is green, including **Release**.
5. If the run is not green, select **Run pipeline**.
6. Select the `main` branch.
7. Select **Run**.
8. Wait for the **Release** stage to finish.

**Verify:**

1. The **Release** stage shows **Publish the package to the splunk-apps
   feed** as succeeded, or `already in the splunk-apps feed, skipping
   publish`.

## Start the deploy

**Do:**

1. Select **Pipelines**.
2. Open `deploy-apps`.
3. Select **Run pipeline**.
4. Select `prod` for **Environment**.
5. Type the app ids, separated by spaces, in **App IDs**.
6. Leave **DANGER - Uninstall each app first. PERMANENTLY DELETES ALL of its
   lookups (CSV files) and local settings** unchecked.
   **DANGER:** checking it deletes every lookup (CSV file) and every local
   setting of each app on prod before the install, with no undo. See
   [Deploy pipeline](/Pipelines/Deploy-pipeline).
7. If you want a restart after installs when ACS requires it, check
   **Restart both search heads at the end if required**.
8. Select **Run**.
9. Wait until every **Compare `<app-id>` with prod** stage is green.

**Verify:**

1. The run shows **Compare**, **Uninstall**, and **Install** stages according
   to the selected options.
2. Each **Install `<app-id>` on prod** stage shows **Waiting** for review.
3. The **Restart prod if required after the uninstalls** stage appears when
   the DANGER uninstall option is checked and app IDs are given.
4. The **Restart prod if required after the installs** stage appears only when
   the restart checkbox and Install are checked and app IDs are given.

## Deploy an app from its pipeline

After a merge to `main`, the app pipeline runs **Release** before **Deploy to
prod**. The `splunk-prod` approval check gates the prod stage. Nothing installs
without approval. A rejection stops the stage. If nobody approves before
Timeout, Azure marks the stage skipped.

**Do:**

1. Open the app pipeline's `main` run.
2. On **Deploy to prod**, select **Review**.
3. Select **Approve** to allow the prod install.
4. Leave the approval pending to have the stage skip at Timeout.

**Verify:**

1. **Deploy to prod** completes after approval or shows **Skipped** after
   Timeout.

## Review and approve each app

Repeat for every app, one at a time.

**Do:**

1. Open the **Compare `<app-id>` with prod** stage.
2. Open the job **Compare with prod**.
3. Open the step **Compare prod with this package (file tree, local and
   default)**.
4. Read the `[added]` lines. They are files in the package from Azure Repos
   that prod does not have.
5. Read the `[removed]` lines. They are files in prod that the package does
   not have.
6. Open the step **Compare prod with this package (local files vs default)**.
7. Read the diff: red `-` lines are prod local settings; green `+` lines are
   this package's defaults.
8. Open the step **Compare prod with this package (merged defaults)**.
9. Read each file's diff.
10. Open the job **Compare with itsi-prod**.
11. Repeat steps 3 to 9 for the prod ITSI search head. Its local settings are
    what was built by hand there.
12. Return to the run summary.
13. On the **Install `<app-id>` on prod** stage, select **Review**.
14. Select **Approve** if the compare matches what you expect.
15. Select **Reject** if it does not.
16. Wait for the stage to finish before reviewing the next app.

**Verify:**

1. The job **Install on prod** shows each step green: **Install on prod**,
   **Check the installed version**, and **Check stack status after install**.
2. A failed step names the app in its stage and job title.

## Restart stages

The **Restart both search heads at the end if required** checkbox defaults
off. When checked with Install enabled and app IDs provided, it adds a stage
after the installs. That stage runs jobs for the ITSI search head and then the
main search head. Each job restarts only when ACS reports that a restart is
required.

When the DANGER uninstall option is checked and app IDs are provided, the run
adds a separate stage after the uninstalls, even if the restart checkbox is
off. It runs before installs. The jobs check the ITSI search head, then the
main search head, and restart each only when ACS reports that it is required.
If there is no restart stage after installs, **Check stack status after
install** still reports any pending restart.

**Do:**

1. On each **Restart prod if required after the uninstalls** or **Restart prod
   if required after the installs** stage, select **Review**.
2. Select **Approve**.
3. Wait for the stage to finish.

**Verify:**

1. **Restart if required** reports when no restart is required, or completes
   the restart.
2. **Check stack status after restart** shows no restart requirement.

A rejected app does not block the restart stage. To deploy a rejected app
later, start a new run with only that app id.

## Related

- [Deploy pipeline](/Pipelines/Deploy-pipeline)
- [Reading the run log](/Troubleshooting/Reading-logs)
- [Deploy troubleshooting](/Troubleshooting/Deploy)

---

[< Previous: Deploy pipeline](/Pipelines/Deploy-pipeline) |
[Next: Compare pipeline >](/Pipelines/Compare-pipeline)
