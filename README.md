# azure-pipelines-splunk-apps

This repository contains shared Azure Pipelines for Splunk Cloud apps. They
validate packages, deploy to nonprod, compare app files across environments,
and publish versioned releases.

## Installation

### Set up

Start with the [setup checklist](AZURE-DEVOPS-SETUP.md), which links to the
prerequisites and setup procedures.

## Usage

### Check credentials

Run the [smoke test](SMOKE-TEST.md) to check the AppInspect account and both
ACS tokens before the first app pipeline run.

### Run the tests

From the repository root, run:

```sh
python -m unittest discover -s tests -p "test_*.py"
```

The compare pipeline reports the raw file tree, local files against defaults,
and merged-default differences for each app.

## Documentation

The [documentation pages](wiki/Home.md) are also published as the Azure DevOps
wiki.
