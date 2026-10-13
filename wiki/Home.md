# Home

This pipeline packages Splunk apps from each app repo, validates them with
AppInspect as Splunk Cloud private apps, deploys pull request packages to
nonprod, compares them with production, and publishes versioned packages from
`main` with an optional production deployment.

Setup steps are in `AZURE-DEVOPS-SETUP.md` at the root of the
`azure-pipelines-splunk-apps` repository. Open it from **Repos → Files**.

## Contents

1. [How it works](How-it-works.md)
   - [The two repositories](How-it-works.md#the-two-repositories)
   - [Pull request and main runs](How-it-works.md#pull-request-and-main-runs)
   - [Repositories and services](How-it-works.md#repositories-and-services)
2. [Pipeline stages](Pipeline-stages.md)
   - [build](Pipeline-stages.md#build)
   - [appinspect](Pipeline-stages.md#appinspect)
   - [nonprod](Pipeline-stages.md#nonprod)
   - [proddiff](Pipeline-stages.md#proddiff)
   - [release](Pipeline-stages.md#release)
   - [prod](Pipeline-stages.md#prod)
3. [Releases and versions](Releases-and-versions.md)
   - [Version bumps](Releases-and-versions.md#version-bumps)
   - [Tags and feed packages](Releases-and-versions.md#tags-and-feed-packages)
   - [Review the production diff](Releases-and-versions.md#review-the-production-diff)
   - [Compare nonprod with prod](Releases-and-versions.md#compare-nonprod-with-prod)
4. [release.py commands](release.py-commands.md)
5. [Troubleshooting](Troubleshooting.md)

## Find a task

| Task | Page |
| --- | --- |
| See what a pull request run does | [Pipeline stages](Pipeline-stages.md) |
| Find why a stage was skipped | [Pull request and main runs](How-it-works.md#pull-request-and-main-runs) |
| Read an AppInspect report | [appinspect](Pipeline-stages.md#appinspect) |
| Review changes before production | [Review the production diff](Releases-and-versions.md#review-the-production-diff) |
| Compare two environments | [Compare nonprod with prod](Releases-and-versions.md#compare-nonprod-with-prod) |
| Set a major or minor version | [Version bumps](Releases-and-versions.md#version-bumps) |
| Fix a failed run | [Troubleshooting](Troubleshooting.md) |

Each page starts with its own table of contents.
