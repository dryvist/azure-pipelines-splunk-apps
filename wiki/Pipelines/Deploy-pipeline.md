# Deploy pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Deploy pipeline

[[_TOC_]]

## Run path

The pipeline in `deploy/azure-pipelines.yml` takes an environment and
space-separated app ids. Each app gets two stages. A restart stage is optional:
the Run form parameter **Restart the stack after the deploys if a restart is
required** defaults off. The stage appears only when it is checked and app ids
are given. The Run form parameter **Uninstall each app completely before
installing it (removes its local settings)** also defaults off. When checked,
each Deploy stage uninstalls the app before it installs the package. Every
stage and job names the app and environment, so a failure shows where it
happened.

- **Compare `<app-id>` with `<environment>`**, job **Compare `<app-id>` with
  `<environment>` (no install)**: downloads the latest package from
  `splunk-apps`, exports the installed app and compares them. It installs
  nothing.
- **Deploy `<app-id>` to `<environment>`**, job **Install `<app-id>` on
  `<environment>`**: waits for the `splunk-<environment>` approval, then
  installs the package. It does not repeat the compare.
- **Restart `<environment>` if required**, job **Restart `<environment>` if
  required and check status**: appears only when Restart is checked and app ids
  are given. It waits for approval, restarts only when ACS reports
  `messages.restartRequired`, then checks status.

All compare stages start at once. Each deploy stage starts after its own
compare stage. The exclusive lock check on `splunk-<environment>` runs the
deploy stages one at a time. When included, the restart stage runs after every
deploy stage finishes, including rejected ones. If Restart is unchecked, each
app's **Check stack status after deploy** step still reports a pending restart.

Both per-app jobs run `templates/deploy-app.yml`:

- **Use Python 3.13**, **Install diff dependencies** (Compare stage only) and
  **Set up ACS CLI** prepare the agent. See
  [release.py commands](/Reference/Release.py-commands).
- **Check `<app-id>` is in the splunk-apps feed:** Fails with a plain message
  when the feed has no version of the app. Compare stage only.
- **Download `<app-id>` from the splunk-apps feed:** Gets the latest package.
- **Check stack status before deploy:** Reads the selected stack status.
- **Export this app from `<environment>` via ACS:** Exports the installed app.
  An app that is not installed prints `NOT INSTALLED <app-id>`. This step, the
  three compare steps, and the publish step run in the Compare stage only.
- **Compare `<environment>` with this package (file tree, local and
  default):** Writes `<app-id>-tree.txt` with raw file changes.
- **Compare `<environment>` with this package (local files vs default):**
  Writes the local-versus-default report.
- **Compare `<environment>` with this package (merged defaults):** Writes the
  merged-default reports.
- **Publish the `<environment>` compare artifact:** Publishes
  `<environment>-diff-<app-id>-<attempt>`.
- **Uninstall the app from `<environment>` via ACS:** Removes the app and its
  local settings, or prints that it is not installed. Deploy stage only, and
  only when **Uninstall** is checked.
- **Deploy to `<environment>` via ACS:** Installs the package. Deploy stage
  only.
- **Wait for the deployed version:** Confirms the package version. Deploy
  stage only.
- **Check stack status after deploy:** Reads the selected stack status.
  Deploy stage only.

For the full production walkthrough, see
[Deploy to production](/Pipelines/Deploy-to-production).

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Shared per-app steps.](../diagrams/deployment-job.png)

## Related

- [Restart pipeline](/Pipelines/Restart-pipeline)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Import from nonprod](/Pipelines/Nonprod-import) |
[Next: Deploy to production >](/Pipelines/Deploy-to-production)
