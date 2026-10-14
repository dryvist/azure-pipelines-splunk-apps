# Home

This pipeline packages apps from each app repo, validates them, deploys pull
request packages to nonprod, compares them with production, and publishes
versioned packages from `main` with an optional production deployment.

Setup steps are in `AZURE-DEVOPS-SETUP.md` at the root of the repository.
Open it from **Repos → Files**.

## Contents

1. [How it works](How-it-works.md)
   - [The two repositories](How-it-works.md#the-two-repositories)
   - [Run paths](How-it-works.md#run-paths)
   - [Pull request run](How-it-works.md#pull-request-run)
   - [Main run](How-it-works.md#main-run)
   - [One deployment job](How-it-works.md#one-deployment-job)
   - [How the diff is built](How-it-works.md#how-the-diff-is-built)
   - [Smoke-test jobs](How-it-works.md#smoke-test-jobs)
   - [Variable group use](How-it-works.md#variable-group-use)
2. [Pipeline stages](Pipeline-stages.md)
   - [Main app pipeline](Pipeline-stages.md#main-app-pipeline)
   - [build](Pipeline-stages.md#stage-build)
   - [appinspect](Pipeline-stages.md#stage-appinspect)
   - [nonprod](Pipeline-stages.md#stage-nonprod)
   - [proddiff](Pipeline-stages.md#stage-proddiff)
   - [release](Pipeline-stages.md#stage-release)
   - [prod](Pipeline-stages.md#stage-prod)
   - [Compare pipeline](Pipeline-stages.md#compare-pipeline)
   - [Smoke-test pipeline](Pipeline-stages.md#smoke-test-pipeline)
3. [Releases and versions](Releases-and-versions.md)
   - [Version bumps](Releases-and-versions.md#version-bumps)
   - [Tags and feed packages](Releases-and-versions.md#tags-and-feed-packages)
   - [Review the production diff](Releases-and-versions.md#review-the-production-diff)
   - [Compare nonprod with prod](Releases-and-versions.md#compare-nonprod-with-prod)
4. [release.py commands](release.py-commands.md)
5. [Troubleshooting](Troubleshooting.md)
   - [Before the first stage](Troubleshooting.md#before-the-first-stage)
   - [Agent setup and network access](Troubleshooting.md#agent-setup-and-network-access)
   - [Build stage](Troubleshooting.md#build-stage)
   - [AppInspect stage](Troubleshooting.md#appinspect-stage)
   - [Nonprod stage](Troubleshooting.md#nonprod-stage)
   - [Proddiff stage](Troubleshooting.md#proddiff-stage)
   - [Release stage](Troubleshooting.md#release-stage)
   - [Prod stage](Troubleshooting.md#prod-stage)
   - [Compare pipeline](Troubleshooting.md#compare-pipeline)
   - [Smoke-test pipeline](Troubleshooting.md#smoke-test-pipeline)
   - [Read the run log](Troubleshooting.md#read-the-run-log)

## Find a task

| Task | Page |
| --- | --- |
| See every stage, job, and step | [Pipeline stages](Pipeline-stages.md) |
| Follow the pull request or main run | [Run paths](How-it-works.md#run-paths) |
| Find why a stage was skipped | [Troubleshooting](Troubleshooting.md#a-stage-after-appinspect-is-skipped) |
| Authorize a variable group or environment | [Resource permissions](Troubleshooting.md#variable-group-not-found-or-not-authorized) |
| Fix an AppInspect login or finding | [AppInspect stage](Troubleshooting.md#appinspect-stage) |
| Fix an ACS token or capability | [ACS troubleshooting](Troubleshooting.md#acs-token-is-rejected-or-lacks-access) |
| Allow agent addresses for ACS | [ACS allowlist](Troubleshooting.md#agent-address-is-missing-from-the-acs-allowlist) |
| Fix a search head | [Compare pipeline](Troubleshooting.md#search-head-is-empty-or-not-configured) |
| Review the production diff | [Review the production diff](Releases-and-versions.md#review-the-production-diff) |
| Compare nonprod with prod | [Compare pipeline](Pipeline-stages.md#compare-pipeline) |
| Run the read-only smoke test | [Smoke-test pipeline](Pipeline-stages.md#smoke-test-pipeline) |
| Read pipeline commands and warnings | [Run log](Troubleshooting.md#read-the-run-log) |

Each page starts with its own table of contents.
