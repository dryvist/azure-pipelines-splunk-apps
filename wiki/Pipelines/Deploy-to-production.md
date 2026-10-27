# Deploy to production

Deploy a set of apps to prod. Review each app's compare, then approve one shared install.

## Prepare

1. On the workstation, run `git sync` in the `azure-pipelines-splunk-apps` folder.
2. Select **Pipelines → Environments**.
3. Open `splunk-prod`.
4. Select **Approvals and checks**.
5. Confirm the list shows **Approvals** and **Exclusive Lock**.
6. If either check is missing, add it. See [Environments and ACS access](/Getting-started/Environments-and-ACS).
7. Confirm the **Approvals** check has a **Timeout** of `12 hours`.

## Release each app

1. Select **Pipelines**, then open the app's pipeline.
2. Open the latest run on `main`.
3. Confirm every stage is green, including **Release**.
4. If the run is not green, select **Run pipeline**, select `main`, and select **Run**.
5. Wait for the **Release** stage to finish. See [Release stage](/Stages/Release).

## Start the deployment

1. Open `deploy-apps` in **Pipelines**.
2. Select **Run pipeline**.
3. Select `prod` for **Environment**.
4. Enter the app IDs, separated by `;`, in **App IDs**.
5. Leave the **DANGER - Uninstall each app first** option unchecked. Checking it deletes every lookup
   and local setting of each app on prod, with no undo.
6. Check **Restart both search heads at the end if required** to restart after installs when ACS requires it.
7. Select **Run**.
8. Wait until every **Compare `<app-id>` with prod** stage is green.

## Review each compare

Repeat for each app's **Compare** stage.

1. Open the **Compare `<app-id>` with prod** stage.
2. Open the job **Compare with prod**.
3. Open the step **Compare prod with this package (file tree, local and default)**.
4. Read the `[added]` lines. They are files in the package that prod does not have.
5. Read the `[removed]` lines. They are files in prod that the package does not have.
6. Open the step **Compare prod with this package (local files vs default)**.
7. Read the diff. Red `-` lines are prod local settings. Green `+` lines are this package's defaults.
8. Open the step **Compare prod with this package (merged defaults)**. Read each file's diff.
9. Open the job **Compare with itsi-prod**. Repeat steps 3 to 8 for the prod ITSI search head.

## Approve and install

1. Return to the run summary. Wait for every compare stage to succeed.
2. If uninstall was selected, approve the uninstall stage and its restart stage. Install waits for them.
3. Open **Install apps on prod** and select **Review**.
4. Select **Approve** to install the selected apps, or **Reject** to stop the install.
5. Wait for the **Install on prod** job. Confirm each step is green.

## Restart stages

- The **Restart prod if required after the installs** stage needs the restart checkbox, **Install apps**, and app IDs. Select **Review**, then **Approve**.
- The **Restart prod if required after the uninstalls** stage needs the DANGER option and app IDs. Select **Review**, then **Approve**.

For stage order and the DANGER option, see [Deploy pipeline](/Pipelines/Deploy-pipeline).

## One app from its pipeline

After a merge to `main`, the app pipeline runs **Release** before **Deploy to prod**.

1. Open the app pipeline's `main` run.
2. On **Deploy to prod**, select **Review**.
3. Select **Approve** to allow the install, or **Reject** to stop it now.
4. To let the stage skip, leave the approval pending until its Timeout.

## If a stage fails

A failed compare skips its dependent stages. A rejected or failed uninstall or install skips the stages
after it, including the restart. To deploy a rejected app later, start a new run with only that app ID.

If a release, compare, approval, or install fails, use [Deploy troubleshooting](/Troubleshooting/Deploy).
