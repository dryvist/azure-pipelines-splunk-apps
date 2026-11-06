# Azure CLI shortcuts for these pipelines. Load with: . .\az-helpers.ps1
# Needs az, the azure-devops extension and saved defaults: az devops configure --defaults organization=<url> "project=<name>"

$AzProject = ((az devops configure --list) -match '^project\s*=' -replace '^project\s*=\s*', '').Trim()
if (-not $AzProject) { Write-Warning "No default project. Run: az devops configure --defaults ""project=<name>""" }

function azq { az @args --only-show-errors }
$AzTemp = [IO.Path]::GetTempPath()
function stamp { Get-Date -Format "yyyy-MM-dd HH:mm:ss" }

# Every pipeline ID. Pipelines without the parameter a command sends refuse the run before it starts.
function Get-PipelineIds { azq pipelines list --query "[].id" -o tsv }

# Lets every pipeline use one variable group, such as splunk-itsi-prod. The ID is in its Library page address.
function Grant-Pipelines([Parameter(Mandatory)][int]$GroupId) {
  $pipelines = @(Get-PipelineIds | ForEach-Object { @{ id = [int]$_; authorized = $true } })
  ConvertTo-Json @{ pipelines = $pipelines } -Depth 3 | Set-Content "$AzTemp/az-permissions.json"
  azq devops invoke --area pipelinePermissions --resource pipelinePermissions --http-method PATCH `
    --route-parameters "project=$AzProject" resourceType=variablegroup resourceId=$GroupId `
    --in-file "$AzTemp/az-permissions.json" --api-version 7.1-preview -o none
}

# Starts the import on every app pipeline; each opens its own pull request. Prints one line per pipeline.
# Other pipelines refuse the run before it starts, so they print SKIPPED.
function Import-AllApps([ValidateSet("prod", "nonprod")]$From = "prod", [switch]$Lookups) {
  $params = @(@{ prod = "importFromProd=true"; nonprod = "importFromNonprod=true" }[$From])
  if ($Lookups) { $params += "importLookups=true" }
  $started = 0
  azq pipelines list --query "[].[id, name]" -o tsv | ForEach-Object {
    $id, $name = $_ -split "`t"
    $out = azq pipelines run --id $id --branch main --parameters @params --query buildNumber -o tsv 2>&1
    if ($LASTEXITCODE -eq 0) { "$(stamp) STARTED $name run $out"; $started++ }
    else { "$(stamp) SKIPPED $name - not an app pipeline, or its azure-pipelines.yml has no import option" }
  }
  "$(stamp) Result: $started import runs started. Each opens a pull request in its app repository."
}

function pending {
  azq devops invoke --area pipelines --resource approvals --route-parameters "project=$AzProject" `
    --query-parameters state=pending --api-version 7.1 @args
}

# The approvals waiting for you, with the pipeline each belongs to.
function Get-PendingApprovals { pending --query "value[].{pipeline:pipeline.name, run:pipeline.owner.name, since:createdOn}" -o table }

# The stage an approval waits on, from its run's timeline. Empty when it cannot be found.
function approval-stage($Approval) {
  $records = (azq devops invoke --area build --resource timeline --api-version 7.1 -o json `
    --route-parameters "project=$AzProject" buildId=$($Approval.build) | ConvertFrom-Json).records
  $record = $records | Where-Object id -eq $Approval.id
  while ($record -and $record.type -ne "Stage") { $record = $records | Where-Object id -eq $record.parentId }
  $record.name
}

# Approves the approvals waiting for you, except any stage whose name says prod. Prod stays manual in the web page.
function Approve-All {
  $approve = @()
  @(pending --query "value[].{id:id, build:pipeline.owner.id, pipeline:pipeline.name}" -o json | ConvertFrom-Json) |
    ForEach-Object {
      $stage = approval-stage $_
      if ($stage -and $stage -notmatch '\bprod\b') { "$(stamp) APPROVE $($_.pipeline): $stage"; $approve += $_.id }
      else { "$(stamp) SKIPPED $($_.pipeline): $(if ($stage) { $stage } else { 'stage not found' }) - approve it in the web page" }
    }
  if (-not $approve) { "$(stamp) Result: nothing to approve"; return }
  ConvertTo-Json -InputObject @($approve | ForEach-Object { @{ approvalId = $_; status = "approved"; comment = "Approve-All" } }) |
    Set-Content "$AzTemp/az-approvals.json"
  azq devops invoke --area pipelines --resource approvals --route-parameters "project=$AzProject" --http-method PATCH `
    --in-file "$AzTemp/az-approvals.json" --api-version 7.1 -o none
  "$(stamp) Result: $($approve.Count) approved"
}

# The last runs of every pipeline with the options each started with.
function Get-RecentRuns([int]$Top = 30) {
  azq pipelines runs list --top $Top -o table `
    --query "[].{pipeline:definition.name, run:buildNumber, result:result, options:to_string(templateParameters)}"
}
