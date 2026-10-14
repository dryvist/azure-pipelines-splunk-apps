# Deploy pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Deploy pipeline

[[_TOC_]]

## Run path

The pipeline in `deploy/azure-pipelines.yml` accepts an environment and
space-separated app ids. It uses the matching `splunk-<environment>` group
and deployment environment. Production deploys use `splunk-prod` and require
the deployment environment's configured approvals. For each app, it downloads
the latest package from `splunk-apps` and runs
`templates/deploy.yml`. After all packages succeed, it restarts the stack only
when ACS reports `messages.restartRequired` as true, then checks status.

The deploy job checks out the tools repo, selects Python 3.13, installs the
diff dependencies once, and includes shared ACS setup before the per-app
steps. See [release.py commands](/Reference/Release.py-commands) for the
ACS setup lifecycle. The job runs these steps for each app:

- **Check stack status before deploy:** Reads the selected stack status.
- **Export this app from `<environment>` via ACS:** Exports the installed app.
- **Compare `<environment>` with this package (local files vs default):**
  Writes the local-versus-default report.
- **Compare `<environment>` with this package (merged defaults):** Writes the
  merged-default reports.
- **Publish:** Publishes `<environment>-diff-<app>-<attempt>`.
- **Deploy to `<environment>` via ACS:** Installs the package.
- **Wait for the deployed version:** Confirms the package version.
- **Check stack status after deploy:** Reads the selected stack status.

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Shared per-app steps.](../diagrams/deployment-job.png)

## Related

- [Restart pipeline](/Pipelines/Restart-pipeline)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: App pipeline](/Pipelines/App-pipeline) |
[Next: Compare pipeline >](/Pipelines/Compare-pipeline)
