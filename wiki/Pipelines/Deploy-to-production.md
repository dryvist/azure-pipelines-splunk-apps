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
6. If you want a restart, check **Restart the stack after the deploys if a
   restart is required**.
7. Select **Run**.
8. Wait until every **Compare `<app-id>` with prod** stage is green.

**Verify:**

1. The run shows one **Compare** stage and one **Deploy** stage per app.
2. Each **Deploy `<app-id>` to prod** stage shows **Waiting** for review.
3. The **Restart prod if required** stage appears only when Restart is checked
   and app ids are given.

## Deploy an app from its pipeline

After a merge to `main`, the app pipeline runs **Release** before **Deploy to
prod**. The `splunk-prod` approval check gates the prod stage. Nothing installs
without approval. A rejection stops the stage. If nobody approves before
Timeout, Azure marks the stage skipped.

**Do:**

1. Open the app pipeline's `main` run.
2. On **Deploy to prod**, select **Review**.
3. Select **Approve** to allow the prod compare and install.
4. Leave the approval pending to have the stage skip at Timeout.

**Verify:**

1. **Deploy to prod** completes after approval or shows **Skipped** after
   Timeout.

## Review and approve each app

Repeat for every app, one at a time.

**Do:**

1. Open the **Compare `<app-id>` with prod** stage.
2. Open the job **Compare `<app-id>` with prod (no install)**.
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
10. Return to the run summary.
11. On the **Deploy `<app-id>` to prod** stage, select **Review**.
12. Select **Approve** if the compare matches what you expect.
13. Select **Reject** if it does not.
14. Wait for the stage to finish before reviewing the next app.

**Verify:**

1. The job **Install `<app-id>` on prod** shows each step green: **Deploy to
   prod via ACS**, **Wait for the deployed version** and **Check stack status
   after deploy**.
2. A failed step names the app in its stage and job title.

## Restart (optional)

The **Restart the stack after the deploys if a restart is required** checkbox
defaults off. Check it on the Run form if you want a restart stage. It appears
only when checked and app ids are given. If unchecked, each app's **Check stack
status after deploy** step still reports a pending restart.

**Do:**

1. On the **Restart prod if required** stage, select **Review**.
2. Select **Approve**.
3. Wait for the stage to finish.

**Verify:**

1. **Restart the current stack** prints that no restart is required, or
   finishes the restart.
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
