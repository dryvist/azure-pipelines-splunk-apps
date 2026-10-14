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
ACS CLI and diff dependencies once, then runs the shared steps for each app:

- Check status and export the installed app.
- Create and publish `<environment>-diff-<app>-<attempt>`.
- Install the package, wait for its version, and check status again.

![Manual deploy pipeline flow.](../diagrams/deploy-pipeline.png)

![Shared per-app steps.](../diagrams/deployment-job.png)

## Related

- [Restart pipeline](/Pipelines/Restart-pipeline)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: App pipeline](/Pipelines/App-pipeline) |
[Next: Compare pipeline >](/Pipelines/Compare-pipeline)
