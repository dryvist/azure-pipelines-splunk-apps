# Azure CLI

`az-helpers.ps1`, in the root of this repository, adds short PowerShell commands that start the app pipelines in bulk
and approve their waiting stages. It reads your organization and project from your Azure CLI defaults.

## Set up once

1. Open PowerShell.
2. Run `winget install --exact --id Microsoft.AzureCLI`. If `winget` is blocked, follow
   [Install the ZIP version](#install-the-zip-version) instead.
3. Close PowerShell and open a new window.
4. Run `az login`.
5. Run `az extension add --name azure-devops`.
6. Run `az devops configure --defaults organization=https://dev.azure.com/<org> "project=<project>"`.
7. Run `az devops configure --list` and confirm both values.

### Install the ZIP version

This needs no admin rights.

1. Run `iwr https://aka.ms/installazurecliwindowszipx64 -OutFile $HOME\azcli.zip`.
2. Run `Expand-Archive $HOME\azcli.zip $HOME\AzureCLI`.
3. Run this to add its `bin` folder to your user `Path`:

   ```powershell
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$HOME\AzureCLI\bin", "User")
   ```

4. Close every PowerShell and VS Code window, then open a new one.
5. Run `az version` from any folder.

If `az` is not found, run `dir $HOME\AzureCLI -Recurse -Filter az.cmd` and use the folder it shows in step 3.

## Load the commands

1. Run `cd <your clone of azure-pipelines-splunk-apps>`.
2. Run `. .\az-helpers.ps1`. The leading dot and space are part of the command.

To load them in every new window, add that line with the full path to the file that `notepad $PROFILE` opens.

## Commands

| Command | What it does |
| --- | --- |
| `Get-PipelineIds` | Lists every pipeline ID. |
| `Grant-Pipelines -GroupId <id>` | Lets every pipeline use one variable group. The ID is in the group's Library page address. |
| `Import-AllApps` | Starts the prod import on every app pipeline, one `STARTED` or `SKIPPED` line each. Add `-From nonprod` or `-Lookups`. |
| `Get-PendingApprovals` | Lists the approvals waiting for you, with their pipeline and run. |
| `Approve-All` | Approves the waiting approvals except stages whose name says prod, such as **Deploy to prod**. |
| `Get-RecentRuns` | Shows the last 30 runs and the options each started with. Add `-Top <n>` for more. |

## Import every app from prod

The import runs only read prod and open pull requests. The pull requests' runs deploy to nonprod after the
`splunk-nonprod` approval. Prod changes only when someone starts **Deploy to prod** and approves it in the web page.

1. Run `Grant-Pipelines -GroupId <splunk-itsi-prod id>`.
2. Run `Import-AllApps`.
3. Confirm the last line, `Result: <n> import runs started`. Each app prints `STARTED`. Each other pipeline prints
   `SKIPPED` and does not start.
4. Review each pull request, as in [App: Run an import](/Pipelines/App#run-an-import) steps 9 to 11.
5. Run `Get-PendingApprovals` when the merged pull requests reach their nonprod approval.
6. Run `Approve-All`. It approves the nonprod deploys and prints `SKIPPED` for prod stages; approve those in the
   web page.

An app whose `azure-pipelines.yml` has no import parameter also prints the error. Copy the current example file into
that repository, then start that app from the web page.

For settings outside the apps, run the ACS settings pipeline with `action` set to `pull`, `write` selected and
`environment` set to `prod`.
