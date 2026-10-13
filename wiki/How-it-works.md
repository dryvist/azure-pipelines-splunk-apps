# How it works

## The two repositories

Each app repo contains the app under `package/` and an
`azure-pipelines.yml` file. Its `resources.repositories` entry checks out the
shared tools repo with the alias `tools`. The `extends` entry selects
`templates/splunk-app.yml@tools`. The shared repo contains that template and
`release.py`, which run the same release steps for each app repo.

The app id comes from `[id] name` in `package/default/app.conf`. If that value
is missing, `release.py` uses the Azure Repos repository name, then the
working directory name. The `[launcher]` and `[id]` version values must match.

## Pull request and main runs

Azure Repos queues pull request validation through a `main` branch policy
with Build validation. The YAML `trigger` queues runs for commits to `main`;
Azure Repos ignores YAML `pr:` triggers.

::: mermaid
flowchart LR
    PR["PR validation"] --> Build["build: bump, package"]
    Main["main commit"] --> Build
    Build --> Dist["artifact: dist"]
    Dist --> Inspect["appinspect stage"]
    InspectGroup["variable group: splunk-appinspect"] --> Inspect
    Inspect --> Report["artifact: appinspect-report-N"]
    Inspect -->|"PR and success"| Nonprod["nonprod stage"]
    Dist --> Nonprod
    NonprodGroups["variable groups: splunk-appinspect, splunk-nonprod"] --> Nonprod
    NonprodEnv["environment: splunk-nonprod"] --> Nonprod
    Nonprod --> NonprodNone["no pipeline artifact"]
    Nonprod -->|"success"| Proddiff["proddiff stage"]
    Dist --> Proddiff
    ProdGroup["variable group: splunk-prod"] --> Proddiff
    Proddiff --> ProdDiffArtifact["artifact: prod-diff-N"]
    Inspect -->|"main and success"| Release["release stage"]
    Dist --> Release
    Release --> GitTag["git tag: release version"]
    Release --> Feed["Universal Package: splunk-apps"]
    Release -->|"prod true"| Prod["prod stage"]
    Dist --> Prod
    ProdGroups["variable groups: splunk-appinspect, splunk-prod"] --> Prod
    ProdEnv["environment: splunk-prod"] --> Prod
    Prod --> ProdNone["no pipeline artifact"]
:::

The `dist` artifact carries the package from `build` to later stages. The
`appinspect-report-<attempt>` artifact contains HTML and JSON reports when AppInspect
produces them. A pull request run reaches `proddiff` only after `nonprod`
succeeds. A main run reaches `release` after AppInspect succeeds; the `prod`
stage is included only when the template parameter `prod` is true.

## Repositories and services

::: mermaid
flowchart LR
    AppRepo["app repo: package and YAML"]
    SharedRepo["shared tools repo"]
    AppRepo -->|"alias tools"| SharedRepo
    AppRepo -->|"extends"| Template["templates/splunk-app.yml"]
    SharedRepo --> Template
    SharedRepo --> ReleaseScript["release.py"]
    Template --> InspectAPI["AppInspect API"]
    InspectGroup["variable group: splunk-appinspect"] --> InspectAPI
    Template --> Nonprod["nonprod deployment"]
    NonprodGroup["variable group: splunk-nonprod"] --> Nonprod
    NonprodEnv["environment: splunk-nonprod"] --> Nonprod
    Nonprod -->|"ACS install"| NonprodStack["nonprod stack"]
    Template --> ProdDiff["production export and diff"]
    ProdGroup["variable group: splunk-prod"] --> ProdDiff
    ProdDiff -->|"ACS export"| ProdStack["production stack"]
    ProdDiff --> DiffArtifact["artifact: prod-diff-N"]
    Template --> Prod["optional prod deployment"]
    InspectGroup --> Prod
    ProdGroup --> Prod
    ProdEnv["environment: splunk-prod"] --> Prod
    Prod -->|"ACS install"| ProdStack
    Template --> Release["main release"]
    Release --> GitTags["Azure Repos git tags"]
    Release --> Feed["splunk-apps feed"]
:::

The production export uses ACS to download the installed app with `default`,
`local`, and `users` content. The release stage creates the `v<version>` Git
tag and publishes a Universal Package to the `splunk-apps` feed.
