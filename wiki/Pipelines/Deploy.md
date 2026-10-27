# Deploy pipeline

The Deploy pipeline installs released packages for one or more apps on nonprod or prod. It can also compare,
uninstall, and restart.

The pipeline is named `deploy-apps` in [Manual pipelines](/Setup/Manual-pipelines).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to deploy to. Stages use `splunk-<environment>` and wait for its approval. |
| `apps` | App IDs separated by `;` | empty | Apps to deploy, such as `my_app;other_app`. Each app must be in the splunk-apps feed. |
| `compare` | on, off | on | Compare each app with the environment first. One compare stage per app. |
| `install` | on, off | on | Install each app with one ACS bulk command. |
| `uninstall` | on, off | off | DANGER: uninstall each app first. Read [DANGER: uninstall](#danger-uninstall). |
| `restart` | on, off | off | Restart both search heads at the end, if ACS reports that a restart is required. |

To rerun only part of a deployment, clear the parts that already succeeded. For example, clear `compare`
and `uninstall` to run only the installs.

## Run a deployment

1. Open **Pipelines**, then open `deploy-apps`.
2. Select **Run pipeline**.
3. Select `nonprod` or `prod` for **Environment**.
4. Enter the app IDs, separated by `;`, in **App IDs separated by ;**.
5. Keep **Compare each app with the environment first** and **Install each app** selected, unless you are
   rerunning part of a deployment.
6. Select **Restart both search heads at the end if required** if the stack should restart after the installs.
7. Select **Run**.
8. Permit each requested variable group and environment. If authorization stopped the run, rerun it. See
   [Permissions](/Troubleshooting/Permissions).
9. Approve each stage that waits. See [Approve a stage](#approve-a-stage).

Verify that the run shows one compare stage per app and one install stage. The install must use the
`splunk-<environment>` approval.

## Stages

- **`compare_<app>`** (Compare `<app>` with `<environment>`): runs when `compare` is on. It waits for
  nothing. All compare stages start at once.
- **`uninstall`** (Uninstall apps from `<environment>`): runs when `uninstall` is on and app IDs are set.
  It waits for every compare stage, when `compare` is on, and for the `splunk-<environment>` approval.
- **`restart_uninstall`** (Restart `<environment>` if required after the uninstalls): runs when `uninstall`
  is on and app IDs are set, whatever `restart` is. It waits for `uninstall`.
- **`install`** (Install apps on `<environment>`): runs when `install` is on and app IDs are set. It waits
  for every compare stage, when `compare` is on. It also waits for `restart_uninstall`, when `uninstall` is
  on, and for the approval.
- **`restart`** (Restart `<environment>` if required after the installs): runs when `restart` and `install`
  are on and app IDs are set. It waits for `install`.

Each compare stage runs two jobs in parallel. **Compare with `<environment>`** uses `splunk-<environment>`
and the main search head. **Compare with `itsi-<environment>`** uses `splunk-itsi-<environment>` and the ITSI
search head. Both download the latest package, export the installed app, and compare without installing.
The steps are in [Reference: Stages](/Reference/Stages#compare-steps).

The restart stages restart the ITSI search head first, then the main search head. Each job restarts only
when ACS reports that a restart is required, then checks stack status. See
[Reference: Stages](/Reference/Stages#restart-stage).

The exclusive lock on `splunk-<environment>` runs deployment jobs one at a time. A failed or rejected stage
skips every stage that depends on it. If `restart` is off, **Check stack status after install** still
reports a pending restart.

## Package steps

The uninstall and install stages run these steps for each selected app. They download the packages to one
directory. The compare stages run the first two steps.

- **Use Python 3.13:** prepares the agent.
- **Check `<app-id>` is in the splunk-apps feed:** fails when the feed has no version of the app.
- **Download `<app-id>` from the splunk-apps feed:** gets the latest package.
- **Uninstall from `<environment>`:** when `uninstall` is on, removes every selected app from all search
  heads, including ITSI. Then it confirms each app is gone. It waits up to 15 minutes for the stack.
- **Install on `<environment>`:** installs every selected package with one ACS bulk command.
- **Check the installed version:** confirms the exact package version for each app. It waits up to 15 minutes.
- **Check stack status after install:** reads the stack status in the deploy stage.

## DANGER: uninstall

> **DANGER: uninstalling deletes ALL of each app's lookups.** Every CSV file in each app's `lookups/` folder
> on the stack is deleted with the app. That includes lookups edited or uploaded in Splunk Web. Local
> settings are deleted too. The install that follows puts back only the lookups in each package. There is
> no undo.
>
> Each `<app-id>-merged.tar.gz` file in the compare artifact holds that app's lookups as they were when the
> compare ran. Anything changed after that is lost.

The `apps` type of the [Bulk delete](/Pipelines/Bulk-Delete) pipeline has the same effect.

## Approve a stage

1. Open the run and wait for every compare stage to succeed.
2. If `uninstall` was selected, approve the uninstall stage and its restart stage. The install waits for them.
3. Open the stage, for example **Install apps on prod**, and select **Review**.
4. Select **Approve** to continue, or **Reject** to stop the stage.
5. Wait for the job to finish. Confirm each step is green.

Restart stages need the same steps: select **Review**, then **Approve**.

## Deploy to prod

### Before you start

1. Pull the latest `main` into your local clone of `azure-pipelines-splunk-apps`.
2. Confirm that `splunk-prod` has the **Approvals** and **Exclusive Lock** checks. See
   [Environments and ACS](/Setup/Environments-and-ACS).
3. For each app, open its pipeline and the latest run on `main`. Confirm every stage is green, including
   **Release**.
4. If a run is not green, select **Run pipeline**, select `main`, select **Run**, and wait for the
   **Release** stage to finish. See [App: Check a release](/Pipelines/App#check-a-release).

### Start the deployment

1. Open `deploy-apps` in **Pipelines** and select **Run pipeline**.
2. Select `prod` for **Environment**.
3. Enter the app IDs, separated by `;`, in **App IDs separated by ;**.
4. Leave **DANGER - Uninstall each app first** unchecked.
5. Check **Restart both search heads at the end if required** to restart after the installs when ACS requires it.
6. Select **Run**, then wait until every **Compare `<app-id>` with prod** stage is green.

### Review each compare

1. Open the **Compare `<app-id>` with prod** stage, then the job **Compare with prod**.
2. Open **Compare prod with this package (file tree, local and default)**. The `[added]` lines are files in
   the package that prod does not have. The `[removed]` lines are files in prod that the package does not have.
3. Open **Compare prod with this package (local files vs default)**. Red `-` lines are prod local settings.
   Green `+` lines are the package's defaults.
4. Open **Compare prod with this package (merged defaults)** and read each file's diff.
5. Open the job **Compare with itsi-prod** and repeat steps 2 to 4 for the prod ITSI search head.

### Approve and install

1. Return to the run summary and wait for every compare stage to succeed.
2. Approve the uninstall stage and its restart stage, if `uninstall` was selected.
3. Approve **Install apps on prod** as described in [Approve a stage](#approve-a-stage).
4. Wait for the **Install on prod** job and confirm each step is green.

If a compare fails, its dependent stages are skipped. If an uninstall or install is rejected or fails, the
stages after it are skipped, including the restart. To deploy a rejected app later, start a new run with
only that app ID. For failures, see [Deploy troubleshooting](/Troubleshooting/Deploy).

## Sharing

Knowledge object sharing (private, app, or global) is set in each app's `metadata/default.meta`. The app
deploys with that setting. ACS app-level read and write roles are managed in the separate ACS config
repository.

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Compare and deployment job steps.](../diagrams/deployment-job.png)
