# How it works

[[_TOC_]]

## The two repositories

Each app repo contains the app under `package/` and an
`azure-pipelines.yml` file. Its `resources.repositories` entry checks out the
shared tools repo with the alias `tools`. The `extends` entry selects
`templates/splunk-app.yml@tools`. The shared repo contains that template and
`release.py`, which run the same release steps for each app repo.

The app id comes from `[id] name` in `package/default/app.conf`. If that value
is missing, `release.py` uses the Azure Repos repository name, then the
working directory name. The `[launcher]` and `[id]` version values must match.

## Run paths

Azure Repos queues pull request validation through a Build Validation policy
on the target branch. The YAML `trigger` queues runs for commits to `main`.
Azure Repos ignores YAML `pr:` triggers. The `Show stage plan` step in the
build job prints the reason for each stage decision.

### Pull request run

![Pull request flow through build, AppInspect, nonprod, and proddiff.](diagrams/pr-run.png)

The `nonprod` stage and `proddiff` run on pull requests and `main`. A pull
request does not meet the `release` stage condition.

### Main run

![Main branch flow through build, AppInspect, release, nonprod, and proddiff.](diagrams/main-run.png)

The `release` stage requires `Build.SourceBranch` to equal
`refs/heads/main`. Production installation runs through the separate manual
deploy pipeline.

## Shared deploy steps

The `nonprod` deployment job and the manual deploy pipeline use the same
`templates/deploy.yml` steps. Each deployment selects its environment and
variable groups.

![Shared deployment steps for one app.](diagrams/deployment-job.png)

## How the diff is built

The target is the installed environment. The source is the package or source
environment. The diff report preserves local-versus-default details before
merging local configuration.

![Diff construction from target and package to comparison outputs.](diagrams/diff-build.png)

The patch compares `default/` and `metadata/default.meta`. The summary also
lists local and user files. The merged archive omits `local/`,
`metadata/local.meta`, and `users/`.

## Smoke-test jobs

The manual smoke-test pipeline checks credentials and read-only ACS export
access. The `result` job runs even when another job fails.

![Smoke test access checks feeding the result summary.](diagrams/smoke-test-jobs.png)

## Variable group use

The target selection for the compare and smoke-test pipelines is `splunk` or
`splunk-itsi`. The `splunk-itsi` groups include a search head setting.

![Pipeline configuration groups and their stage use.](diagrams/variable-group-use.png)

The app pipeline uses `splunk-appinspect` in `appinspect` and `nonprod`,
`splunk-nonprod` in `nonprod`, and `splunk-prod` in `proddiff`. The manual
deploy pipeline uses `splunk-appinspect` and the selected environment group.
The smoke-test pipeline also uses `splunk-appinspect` in `appinspect`.
Compare and smoke-test select `splunk-nonprod` and `splunk-prod` when
`target` is `splunk`. They select `splunk-itsi-nonprod` and
`splunk-itsi-prod` when `target` is `splunk-itsi`.

The `dist` artifact carries the package between stages. AppInspect and diff
artifacts include the job attempt number. See
[Pipeline stages](Pipeline-stages.md) for each job's inputs and outputs.
