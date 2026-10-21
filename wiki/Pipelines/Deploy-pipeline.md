# Deploy pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Deploy pipeline

[[_TOC_]]

## Run path

The pipeline in `deploy/azure-pipelines.yml` takes an environment and
space-separated app ids. Each app gets two stages. A restart stage is optional:
the Run form parameter **Restart the stack after the deploys if a restart is
required** defaults off. The stage appears only when it is checked and app ids
are given. The Run form parameter **DANGER - Uninstall each app first.
PERMANENTLY DELETES ALL of its lookups (CSV files) and local settings** also
defaults off. When checked, each Deploy stage first uninstalls the app from the
ITSI search head, then from the main search head, then installs the package.
Every stage and job names the app and environment, so a failure shows where it
happened.

- **Stage `compare_<app>` (Compare `<app-id>` with `<environment>`):** runs
  two jobs in parallel. **Compare with `<environment>` (no install)** uses
  `splunk-<environment>`, the search head the install replaces.
  **Compare with `itsi-<environment>` (no install)** uses
  `splunk-itsi-<environment>`, the ITSI search head. Both download the latest
  package, export the installed app, and compare without installing.
- **Stage `deploy_<app>` (Deploy `<app-id>` to `<environment>`):** has the
  deployment job **Install on `<environment>`**. It waits for the
  `splunk-<environment>` approval, then installs the package. With the DANGER
  uninstall option, the job **Uninstall from `itsi-<environment>`** runs first
  with the `splunk-itsi-<environment>` group, after the same approval. The
  install job is then named **Uninstall and install on `<environment>`** and
  uninstalls from the main search head before it installs. It does not compare
  the package.
- **Restart `<environment>` if required**, job **Restart `<environment>` if
  required and check status**: appears only when Restart is checked and app ids
  are given. It waits for approval, restarts only when ACS reports
  `messages.restartRequired`, then checks status.

All compare stages start at once. Each deploy stage starts after its matching
compare stage. The exclusive lock check on `splunk-<environment>` runs the
deploy stages one at a time. When included, the restart stage runs only after
every deploy stage succeeds; a failed or rejected deploy stage skips it. If
Restart is unchecked, each app's **Check stack status after deploy** step still
reports a pending restart.

Both stages use `templates/feed-package.yml` to check the feed and download
the latest package. Compare stages use `templates/compare-stage.yml`. Deploy
stages use `templates/deploy-stage.yml`:

- **Use Python 3.13:** Prepares the agent in both stages.
- **Check `<app-id>` is in the splunk-apps feed:** Fails when the feed has no
  version of the app. Runs in both stages.
- **Download `<app-id>` from the splunk-apps feed:** Gets the latest package
  in both stages.
- **Install diff dependencies:** Installs the compare tools in both compare
  jobs.
- **Set up ACS CLI:** Prepares the ACS session in both stages. See
  [release.py commands](/Reference/Release.py-commands).
- **Check stack status before deploy:** Reads the selected stack status in
  both stages.
- **Export this app from `<side>` via ACS:** Exports the installed app
  in each compare job. An app that is not installed prints
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
- **Uninstall the app from `itsi-<environment>` via ACS**, then
  **Uninstall the app from `<environment>` via ACS:** When the DANGER uninstall
  option is checked, first remove the copy installed on the ITSI search head
  only (`--scope local`), then remove the app from all search heads. After each uninstall, the step restarts that search head
  when ACS reports `restartRequired`, and waits until the restart clears and
  the stack is Ready. Deploy stage only. The `splunk-itsi-<environment>` ACS
  token needs the same app install capabilities as the main token.
- **Deploy to `<environment>` via ACS:** Installs the package in the deploy
  stage.
- **Wait for the deployed version:** Confirms the package version in the
  deploy stage.
- **Check stack status after deploy:** Reads the selected stack status in the
  deploy stage.

> **DANGER: uninstalling deletes ALL of the app's lookups.** Every CSV file in
> the app's `lookups/` folder on the stack, including lookups people edited or
> uploaded in Splunk Web, is deleted with the app, along with all of its local
> settings. The install that follows puts back only the lookups in the
> package. There is no undo. The `<app-id>-merged.tar.gz` file in the compare
> artifact holds the lookups as they were when the compare ran; anything
> changed after that is lost.

For the full production walkthrough, see
[Deploy to production](/Pipelines/Deploy-to-production).

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Compare and deployment job steps.](../diagrams/deployment-job.png)

## Related

- [Restart pipeline](/Pipelines/Restart-pipeline)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Import from nonprod or prod](/Pipelines/App-import) |
[Next: Deploy to production >](/Pipelines/Deploy-to-production)
