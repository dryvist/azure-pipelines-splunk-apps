# azure-pipelines-splunk-apps

Shared Azure Pipelines templates and Python release tools for packaging,
validating, comparing, and deploying Splunk Cloud apps.

## Repository contents

- `templates/`: reusable app, deploy, compare, restart, and smoke-test steps.
- `compare/`, `deploy/`, `restart/`, `smoke-test/`: manual pipeline definitions.
- `example/`: app repository pipeline example.
- `release.py` and `splunk_release/`: packaging, AppInspect, ACS, and compare commands.
- `tests/`: Python unit tests.
- `wiki/`: setup, pipeline, stage, troubleshooting, and reference pages.

## Quick start

Copy `example/azure-pipelines.yml` into an app repository, then follow the
[getting-started guide](wiki/Getting-started.md).

## Full documentation

- [Wiki home](wiki/Home.md)
- [Getting started](wiki/Getting-started.md)
- [Pipeline guides](wiki/Pipelines.md)
- [Stage guides](wiki/Stages.md)
- [Troubleshooting](wiki/Troubleshooting.md)
- [Reference](wiki/Reference.md)
