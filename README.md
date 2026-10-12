# azure-pipelines-splunk-apps

This repository provides a shared Azure Repos and Azure Pipelines release
pipeline for Splunk Cloud apps. It validates app packages, compares pull
request packages with production, and publishes versioned releases.

## Installation

### Set up

Follow the [Azure DevOps setup guide](AZURE-DEVOPS-SETUP.md) to configure the
shared repository, feed, variable groups, environments, app repository, and
pipeline.

## Usage

### Copy from GitHub into Azure Repos

Replace `<org>` and `<project>` with your Azure DevOps names. Run these
commands to copy the shared repository:

```sh
git clone https://github.com/dryvist/azure-pipelines-splunk-apps.git
cd azure-pipelines-splunk-apps
git push \
  https://dev.azure.com/<org>/<project>/_git/azure-pipelines-splunk-apps \
  main --tags
```

To update the Azure Repos copy later, run `git pull` in the cloned repository,
then repeat the `git push` command above.

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

Documentation: <https://docs.jacobpevans.com>
