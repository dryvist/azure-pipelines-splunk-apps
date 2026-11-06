# Azure CLI shortcuts for these pipelines. Load with: . .\az-helpers.ps1
# Needs az, the azure-devops extension and saved defaults: az devops configure --defaults organization=<url> "project=<name>"

$AzProject = ((az devops configure --list) -match '^project\s*=' -replace '^project\s*=\s*', '').Trim()
if (-not $AzProject) { Write-Warning "No default project. Run: az devops configure --defaults ""project=<name>""" }

function azq { az @args --only-show-errors }
$AzTemp = [IO.Path]::GetTempPath()

# Pipeline IDs in the \apps folder.
function Get-AppPipelineIds { azq pipelines list --folder-path \apps --query "[].id" -o tsv }

# Moves every pipeline whose repository has a package folder on main into \apps. Run once, and after adding apps.
function Move-AppPipelines {
  azq pipelines folder create --path \apps -o none 2>$null
  azq pipelines list --query "[?path!='\\apps'].id" -o tsv | ForEach-Object {
    $repo = azq pipelines show --id $_ --query repository.id -o tsv
    azq devops invoke --area git --resource items --api-version 7.1 -o none `
      --route-parameters "project=$AzProject" repositoryId=$repo `
      --query-parameters path=/package versionDescriptor.version=main 2>$null
    if ($LASTEXITCODE -eq 0) { azq pipelines update --id $_ --new-folder-path \apps --query name -o tsv }
  }
}

# Lets every app pipeline use one variable group, such as splunk-itsi-prod. The ID is in its Library page address.
function Grant-AppPipelines([Parameter(Mandatory)][int]$GroupId) {
  $pipelines = @(Get-AppPipelineIds | ForEach-Object { @{ id = [int]$_; authorized = $true } })
  ConvertTo-Json @{ pipelines = $pipelines } -Depth 3 | Set-Content "$AzTemp/az-permissions.json"
  azq devops invoke --area pipelinePermissions --resource pipelinePermissions --http-method PATCH `
    --route-parameters "project=$AzProject" resourceType=variablegroup resourceId=$GroupId `
    --in-file "$AzTemp/az-permissions.json" --api-version 7.1-preview -o none
}

# Starts the import on every app pipeline. Each opens its own pull request.
function Import-AllApps([ValidateSet("prod", "nonprod")]$From = "prod", [switch]$Lookups) {
  $params = @(@{ prod = "importFromProd=true"; nonprod = "importFromNonprod=true" }[$From])
  if ($Lookups) { $params += "importLookups=true" }
  Get-AppPipelineIds | ForEach-Object { azq pipelines run --id $_ --branch main --parameters @params --query buildNumber -o tsv }
}

# Approval IDs waiting for you.
function Get-PendingApprovals {
  azq devops invoke --area pipelines --resource approvals --route-parameters "project=$AzProject" `
    --query-parameters state=pending --api-version 7.1 --query "value[].id" -o tsv
}

# Approves every approval waiting for you.
function Approve-All {
  $ids = @(Get-PendingApprovals)
  if (-not $ids) { "Nothing pending"; return }
  "Approving $($ids.Count)"
  ConvertTo-Json -InputObject @($ids | ForEach-Object { @{ approvalId = $_; status = "approved"; comment = "Approve-All" } }) |
    Set-Content "$AzTemp/az-approvals.json"
  azq devops invoke --area pipelines --resource approvals --route-parameters "project=$AzProject" --http-method PATCH `
    --in-file "$AzTemp/az-approvals.json" --api-version 7.1 -o none
}

# The last runs of every pipeline with the options each started with.
function Get-RecentRuns([int]$Top = 30) {
  azq pipelines runs list --top $Top -o table `
    --query "[].{pipeline:definition.name, run:buildNumber, result:result, options:to_string(templateParameters)}"
}
