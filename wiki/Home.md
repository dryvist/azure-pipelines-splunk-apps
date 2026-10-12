# Home

This pipeline packages Splunk apps from each app repo, validates them with
AppInspect as Splunk Cloud private apps, deploys pull request packages to
nonprod, compares them with production, and publishes versioned packages from
`main` with an optional production deployment.

## Pages

- [How it works](How-it-works.md)
- [Pipeline stages](Pipeline-stages.md)
- [Releases and versions](Releases-and-versions.md)
- [Updating from GitHub](Updating-from-GitHub.md)
- [release.py commands](release.py-commands.md)
- [Troubleshooting](Troubleshooting.md)

All setup steps live only in the
[Azure DevOps setup guide](../AZURE-DEVOPS-SETUP.md), the file
`AZURE-DEVOPS-SETUP.md` at the root of the `azure-pipelines-splunk-apps`
repository.
