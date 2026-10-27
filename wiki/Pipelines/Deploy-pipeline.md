# Deploy pipeline

Use this page to see manual deployment parameters, stage order, and restart behavior.

## Run path

The pipeline in `deploy/azure-pipelines.yml` takes an environment and
space-separated app ids. The Run form parameter **DANGER - Uninstall each app
first. PERMANENTLY DELETES ALL of its lookups (CSV files) and local settings**
defaults off. The Run form parameter
**Restart both search heads at the end if required** also defaults off. It
controls the restart stage after installs. The DANGER uninstall option adds a
restart stage after uninstalls, even when this checkbox is off.
**Compare each app with the environment first** and **Install each app** both
default on. Uncheck them to rerun only the part that failed: for example,
uncheck Compare and the DANGER uninstall option to run only the installs.
Compare stages name each app and the environment. Uninstall, install, and
restart stages name the environment.

The stages run in this order. A run can restart at two points. Each restart
happens only when ACS reports that it is required:

1. **Stage `compare_<app>` (Compare `<app-id>` with `<environment>`)**, one
   per app, only with Compare checked: runs two jobs in parallel. **Compare
   with `<environment>`** uses `splunk-<environment>`, the main search head.
   **Compare with `itsi-<environment>`** uses `splunk-itsi-<environment>`, the
   ITSI search head. Both download the latest package, export the installed
   app, and compare without installing.
2. **Stage `uninstall` (Uninstall apps from `<environment>`)**, only with the
   DANGER uninstall option: runs one job, **Uninstall from `<environment>`**,
   after the `splunk-<environment>` approval. It downloads every selected
   package into one directory, asks ACS to uninstall all selected apps, then
   confirms every app is gone from every search head, including ITSI. When
   Compare is checked, this stage waits for every compare stage.
3. **Stage `restart_uninstall` (Restart `<environment>` if required after the
   uninstalls)**, whenever the DANGER uninstall option is checked and app IDs
   are provided: runs after `uninstall` succeeds, regardless of the restart
   checkbox. It runs **Restart `itsi-<environment>` if required**, then
   **Restart `<environment>` if required**. Each job restarts only when ACS
   reports that a restart is required, then checks stack status.
4. **Stage `install` (Install apps on `<environment>`)**, only with Install
   checked: runs one job, **Install on `<environment>`**, after the
   `splunk-<environment>` approval. It installs every selected package with
   one ACS bulk command. When Compare is checked, the stage waits for every
   compare stage. When the DANGER uninstall option is checked, it also waits
   for `restart_uninstall` to succeed.
5. **Stage `restart` (Restart `<environment>` if required after the installs)**,
   only when the restart checkbox and Install are checked: runs after `install`
   succeeds. It runs **Restart `itsi-<environment>` if
   required**, then **Restart `<environment>` if required**. Each job restarts
   only when ACS reports that a restart is required, then checks status.

All compare stages start at once. The exclusive lock on
`splunk-<environment>` runs deployment jobs one at a time. The shared uninstall
and install stages and restart jobs wait for the `splunk-<environment>`
approval. A failed or rejected stage skips every stage that depends on it. If
the restart checkbox is off, **Check stack status after install** still reports
a pending restart.

Compare stages use `templates/compare-stage.yml`. The uninstall and install
stages use `templates/deploy-stage.yml`; each runs
`templates/feed-package.yml` for every selected app and downloads those
packages to one directory:

- **Use Python 3.13:** Prepares the agent in both stages.
- **Check `<app-id>` is in the splunk-apps feed:** Fails when the feed has no
  version of the app. Runs in both stages.
- **Download `<app-id>` from the splunk-apps feed:** Gets the latest package
  in both stages.
- **Install diff dependencies:** Installs the compare tools in both compare
  jobs.
- **Set up ACS CLI:** Prepares the ACS session in both stages. See
  [release.py commands](/Reference/Release.py-commands).
- **Check stack status:** Reads the selected stack status before the job's
  other ACS steps.
- **Export the app from `<side>`:** Exports the installed app in each compare
  job. An app that is not installed prints
  `NOT INSTALLED <app-id>`.
- **Compare `<side>` with this package (file tree, local and default):**
  Writes `<app-id>-tree.txt` with raw file changes.
- **Compare `<side>` with this package (local files vs default):**
  Writes the local-versus-default report.
- **Compare `<side>` with this package (merged defaults):** Writes the
  merged-default reports.
- **Compare `<side>` with this package (data models):** Prints each
  changed data model in its own collapsed group.
- **Publish the `<side>` compare artifact:** Publishes
  `<side>-diff-<app-id>-<attempt>` from each compare job.
- **Uninstall from `<environment>`:** Removes every selected app from all
  search heads, including ITSI, when the DANGER uninstall option is checked,
  then confirms each app is gone.
- **Install on `<environment>`:** Installs every selected package with one ACS
  bulk command.
- **Check the installed version:** Confirms the exact package version for each
  selected app.
- **Check stack status after install:** Reads the selected stack status in the
  deploy stage.

Restart stages use `templates/restart-stage.yml` and restart the ITSI search
head before the main search head.

> **DANGER: uninstalling deletes ALL of each app's lookups.** Every CSV file in
> each app's `lookups/` folder on the stack, including lookups edited or
> uploaded in Splunk Web, is deleted with the app, along with its local
> settings. The install that follows puts back only the lookups in each
> package. There is no undo. Each `<app-id>-merged.tar.gz` file in the compare
> artifact holds that app's lookups as they were when the compare ran; anything
> changed after that is lost.

## Sharing

Knowledge object sharing (private/app/global) is set in each app's
`metadata/default.meta` and deployed with the app. ACS app-level read and write
roles are managed in the separate ACS config repository.

For the full production walkthrough, see
[Deploy to production](/Pipelines/Deploy-to-production).

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Compare and deployment job steps.](../diagrams/deployment-job.png)
