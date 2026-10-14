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

::: mermaid
flowchart LR
    Policy[/External: pull request branch policy/] --> Build[Stage: build]
    Build --> Inspect[Stage: appinspect]
    Inspect --> Nonprod[Stage: nonprod]
    Nonprod --> Diff[Stage: proddiff]
    Inspect --> Release[Skipped stage: release on pull request]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Policy step
    class Build,Inspect,Nonprod,Diff stage
    class Release skip
:::

The `nonprod` stage and `proddiff` run on pull requests and `main`. A pull
request does not meet the `release` stage condition.

### Main run

::: mermaid
flowchart LR
    Commit[/External: main branch update/] --> Build[Stage: build]
    Build --> Inspect[Stage: appinspect]
    Inspect --> Release[Stage: release]
    Inspect --> Nonprod[Stage: nonprod]
    Nonprod --> Diff[Stage: proddiff]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Commit step
    class Build,Inspect,Release,Nonprod,Diff stage
:::

The `release` stage requires `Build.SourceBranch` to equal
`refs/heads/main`. Production installation runs through the separate manual
deploy pipeline.

## Shared deploy steps

The `nonprod` deployment job and the manual deploy pipeline use the same
`templates/deploy.yml` steps. Each deployment selects its environment and
variable groups.

::: mermaid
flowchart LR
    Setup([Checkout tools and select Python]) --> Package[(Package directory)]
    Package --> Cli([Install ACS CLI and diff dependencies once])
    Cli --> Status([Check stack status])
    Status --> Export([Export this app])
    Export --> Compare([Diff and publish this app])
    Compare --> Install([Install and wait for package version])
    Install --> After([Check stack status])
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Setup,Cli,Status,Export,Compare,After step
    class Package step
    class Install deploy
:::

## How the diff is built

The target is the installed environment. The source is the package or source
environment. The diff report preserves local-versus-default details before
merging local configuration.

::: mermaid
flowchart LR
    Inputs[(Artifacts: target and source)] --> Local([Step: local vs defaults])
    Local --> Merge([Step: promote local files into defaults])
    Merge --> Sort([Step: sort merged default configuration])
    Sort --> Compare([Step: compare only default files and default metadata])
    Compare --> Reports[(Artifacts: patch, summary, merged archive)]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Inputs,Reports step
    class Local,Merge,Sort,Compare step
:::

The patch compares `default/` and `metadata/default.meta`. The summary also
lists local and user files. The merged archive omits `local/`,
`metadata/local.meta`, and `users/`.

## Smoke-test jobs

The manual smoke-test pipeline checks credentials and read-only ACS export
access. The `result` job runs even when another job fails.

::: mermaid
flowchart LR
    AppInspect([Job: appinspect login]) --> Result([Job: result summary])
    Nonprod([Job: nonprod ACS login and export]) --> Result
    Prod([Job: prod ACS login and export]) --> Result
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class AppInspect,Nonprod,Prod,Result step
:::

## Variable group use

The target selection for the compare and smoke-test pipelines is `splunk` or
`splunk-itsi`. The `splunk-itsi` groups include a search head setting.

::: mermaid
flowchart TD
    AppInspectGroup[/Variable group: splunk-appinspect/]
    NonprodGroup[/Variable group: splunk-nonprod/]
    ProdGroup[/Variable group: splunk-prod/]
    ItsiNonprod[/Variable group: splunk-itsi-nonprod/]
    ItsiProd[/Variable group: splunk-itsi-prod/]
    Main[/External: main app pipeline/]
    Other[/External: compare and smoke-test pipelines/]
    Deploy[/External: manual deploy pipeline/]
    AppInspectGroup --> Main
    AppInspectGroup --> Other
    AppInspectGroup --> Deploy
    NonprodGroup --> Main
    NonprodGroup --> Other
    NonprodGroup --> Deploy
    ProdGroup --> Main
    ProdGroup --> Other
    ProdGroup --> Deploy
    ItsiNonprod --> Other
    ItsiProd --> Other
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class AppInspectGroup,NonprodGroup,ProdGroup,ItsiNonprod,ItsiProd step
    class Main,Other,Deploy step
:::

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
