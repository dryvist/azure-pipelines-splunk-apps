# Azure CLI

`az-helpers.ps1`, in the root of this repository, adds short PowerShell commands that start the app pipelines in bulk
and approve their waiting stages. It reads your organization and project from your Azure CLI defaults.

## Set up once

1. Open PowerShell.
2. Run `winget install --exact --id Microsoft.AzureCLI`.
3. Close PowerShell and open a new window.
4. Run `az login`.
5. Run `az extension add --name azure-devops`.
6. Run `az devops configure --defaults organization=https://dev.azure.com/<org> "project=<project>"`.
7. Run `az devops configure --list` and confirm both values.

If step 2 is blocked, install the ZIP version of the Azure CLI, then add its folder to your user `Path`.

## Load the commands

1. Run `cd <your clone of azure-pipelines-splunk-apps>`.
2. Run `. .\az-helpers.ps1`. The leading dot and space are part of the command.

To load them in every new window, add that line with the full path to the file that `notepad $PROFILE` opens.

## Commands

| Command | What it does |
| --- | --- |
| `Get-PipelineIds` | Lists every pipeline ID. |
| `Grant-Pipelines -GroupId <id>` | Lets every pipeline use one variable group. The ID is in the group's Library page address. |
| `Import-AllApps` | Starts the prod import on every app pipeline. Add `-From nonprod` or `-Lookups`. Other pipelines print one error each and do not start. |
| `Get-PendingApprovals` | Lists the approvals waiting for you. |
| `Approve-All` | Approves every approval waiting for you, in every pipeline. |
| `Get-RecentRuns` | Shows the last 30 runs and the options each started with. Add `-Top <n>` for more. |

## Import every app from prod

1. Run `Grant-Pipelines -GroupId <splunk-itsi-prod id>`.
2. Run `Import-AllApps`.
3. Confirm it prints one run name per app. Each other pipeline prints one `Unexpected parameter` error and does not
   start.
4. Review each pull request, as in [App: Run an import](/Pipelines/App#run-an-import) steps 9 to 11.
5. Run `Get-PendingApprovals` when the merged pull requests reach their nonprod approval.
6. Run `Approve-All`.

An app whose `azure-pipelines.yml` has no import parameter also prints the error. Copy the current example file into
that repository, then start that app from the web page.

For settings outside the apps, run the ACS settings pipeline with `action` set to `pull`, `write` selected and
`environment` set to `prod`.
