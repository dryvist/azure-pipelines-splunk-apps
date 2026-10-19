# App pipeline

[Home](/Home) > [Pipelines](/Pipelines) > App pipeline

[[_TOC_]]

Each app repository contains `package/` and an `azure-pipelines.yml` that
extends `templates/splunk-app.yml` from the shared tools repository, checked
out as `tools`. The template defaults to Python 3.13 and checks out the tools
repository. An app may override `setup` and `pool`.

Azure Repos queues pull request validation through a Build Validation policy.
The YAML `trigger` queues commits to `main`; Azure Repos ignores YAML `pr:`
triggers. `Show stage plan` prints the run reason and stage conditions.

Build and AppInspect run first. Nonprod and Proddiff run on pull requests and
`main`. Release depends on Proddiff and runs only on `main`. The app pipeline
has no production stage; production installation uses manual deployment.

A pull request run that pushes a version bump stops after the build stage.
The bump commit starts a new run that validates the bumped version.

![Pull request flow.](../diagrams/pr-run.png)

![Main branch flow.](../diagrams/main-run.png)

## Related

- [Stages](/Stages)
- [Build stage](/Stages/Build)

---

[Next: Deploy pipeline >](/Pipelines/Deploy-pipeline)
