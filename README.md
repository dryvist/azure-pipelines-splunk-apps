# azure-pipelines-splunk-apps

This repository contains a shared Azure Repos and Azure Pipelines release
pipeline for Splunk Cloud apps. It validates app packages, compares pull
request packages with production, and publishes versioned releases.

## Installation

### Set up

Follow the [Azure DevOps setup guide](AZURE-DEVOPS-SETUP.md) to configure the
shared repository, feed, variable groups, environments, app repository, and
pipeline.

## Usage

### Run the tests

From the repository root, run:

```sh
python test_release.py
```

## Documentation

The [documentation pages](wiki/Home.md) are also published as the Azure DevOps
wiki.

## License

[Apache License 2.0](LICENSE)
