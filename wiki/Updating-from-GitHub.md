# Updating from GitHub

Copy the shared repository to Azure Repos with plain Git. Replace `<org>` and
`<project>` with your Azure DevOps names before running these commands.

```sh
git clone https://github.com/dryvist/azure-pipelines-splunk-apps.git
cd azure-pipelines-splunk-apps
git push \
  https://dev.azure.com/<org>/<project>/_git/azure-pipelines-splunk-apps \
  main --tags
```

For later updates, pull the GitHub changes and push `main` and its tags to
Azure Repos:

```sh
git pull
git push \
  https://dev.azure.com/<org>/<project>/_git/azure-pipelines-splunk-apps \
  main --tags
```

For the first copy, **Repos → Import repository** can import the GitHub URL.
Sign in through the Git Credential Manager browser prompt or use a PAT with
Code (Read & write).
