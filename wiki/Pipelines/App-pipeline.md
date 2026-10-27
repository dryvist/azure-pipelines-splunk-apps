# App pipeline

Use this page to see how an app pipeline starts, and how its template works.

Each app repository contains `package/` and an `azure-pipelines.yml`. That file extends `templates/splunk-app.yml`
from the shared tools repository, checked out as `tools`. The template defaults to Python 3.13. An app may
override `setup` and `pool`.

Azure Repos queues pull request validation through a Build Validation policy. The YAML `trigger` queues runs for
commits to `main`. Azure Repos ignores YAML `pr:` triggers. **Show stage plan** prints the run reason and the
stage conditions.

For stage order and each stage's inputs, see [Stages](/Stages). For the approval gate on prod, see
[Prod stage](/Stages/Prod). For a pull request run that pushes a version bump, see [Build stage](/Stages/Build).

The template also accepts the `importFromNonprod` and `importFromProd` runtime parameters. Both default to
`false`. When one is selected, the run adds an `import_<env>` stage. That stage exports and compares the app on
the ITSI search head, then opens a pull request. See [Import from nonprod or prod](/Pipelines/App-import).

![Pull request flow.](../diagrams/pr-run.png)

![Main branch flow.](../diagrams/main-run.png)

If a stage skips or fails, use [Build troubleshooting](/Troubleshooting/Build).
