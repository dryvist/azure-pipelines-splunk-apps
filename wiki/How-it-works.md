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
    Release --> Prod[Skipped stage: prod needs a main release]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Policy step
    class Build,Inspect,Nonprod,Diff stage
    class Release,Prod skip
:::

The `nonprod` stage requires a pull request run. `proddiff` follows a
successful `nonprod` stage. A pull request does not meet the `release` stage
condition, so `prod` cannot run.

### Main run

::: mermaid
flowchart LR
    Commit[/External: main branch update/] --> Build[Stage: build]
    Build --> Inspect[Stage: appinspect]
    Inspect --> Release[Stage: release]
    Build --> PRStages[Skipped stages: nonprod and proddiff need a pull request]
    Release --> Enabled{Decision: prod parameter is true}
    Enabled --> Prod[Stage: prod]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Commit step
    class Build,Inspect,Release,Prod stage
    class PRStages skip
    class Enabled risk
:::

The `release` stage requires `Build.SourceBranch` to equal
`refs/heads/main`. The `prod` stage is added only when the app repo sets the
template parameter `prod: true`.

## One deployment job

The `nonprod` and `prod` deployment jobs use the same `templates/deploy.yml`
steps. The selected environment and variable groups differ.

::: mermaid
flowchart LR
    Setup([Step 1: checkout and Python]) --> Package[(Artifact: dist])
    Package --> Cli([Step 2: install and check ACS CLI])
    Cli --> Deps([Step 3: install diff dependencies])
    Deps --> Export([Step 4: export the target app])
    Export --> Compare([Step 5: compare and publish the diff])
    Compare --> Install([Step 6: install the package through ACS])
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Setup,Cli,Deps,Export,Compare step
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
    AppInspectGroup --> Main
    AppInspectGroup --> Other
    NonprodGroup --> Main
    NonprodGroup --> Other
    ProdGroup --> Main
    ProdGroup --> Other
    ItsiNonprod --> Other
    ItsiProd --> Other
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class AppInspectGroup,NonprodGroup,ProdGroup,ItsiNonprod,ItsiProd step
    class Main,Other step
:::

The main pipeline uses `splunk-appinspect` in `appinspect`, `nonprod`, and
`prod`; `splunk-nonprod` in `nonprod`; and `splunk-prod` in `proddiff` and
`prod`. The smoke-test pipeline also uses `splunk-appinspect` in `appinspect`.
Compare and smoke-test select `splunk-nonprod` and `splunk-prod` when
`target` is `splunk`. They select `splunk-itsi-nonprod` and
`splunk-itsi-prod` when `target` is `splunk-itsi`.

The `dist` artifact carries the package between stages. AppInspect and diff
artifacts include the job attempt number. See
[Pipeline stages](Pipeline-stages.md) for each job's inputs and outputs.
