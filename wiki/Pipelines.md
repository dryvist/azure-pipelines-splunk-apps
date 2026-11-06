# Which pipeline?

Find your task in the first column. Set the parameters in the third column. Then open the page in the last column.

Each run's name in the Runs list shows the options it started with, such as `20261105.3 prod 12 apps compare install`.
A list shows as a count. To see every option of recent runs, including full lists, run this in PowerShell:

```powershell
az pipelines runs list --organization https://dev.azure.com/<org> --project <project> --top 30 `
  --query "[].{pipeline:definition.name, run:buildNumber, options:to_string(templateParameters)}" -o table
```

| Task | Pipeline | Parameters to set | Page |
| --- | --- | --- | --- |
| Release a change to one app | App | Open a pull request to `main`, merge it, then approve the prod install | [App](/Pipelines/App) |
| Import every app from prod | App, one run per app | `importFromProd`, from one `az` command | [App](/Pipelines/App#import-every-app-at-once) |
| Deploy one app to nonprod or prod | Deploy | `environment`, `apps` (one ID), `compare`, `install`, `restart` | [Deploy](/Pipelines/Deploy) |
| Deploy several apps | Deploy | `apps` as IDs separated by `;`, such as `app_one;app_two`, plus the options above | [Deploy](/Pipelines/Deploy) |
| Deploy to prod with compare review | Deploy | `environment` = `prod`; approve each compare, then the install | [Deploy](/Pipelines/Deploy#deploy-to-prod) |
| Replace apps (DANGER: deletes lookups) | Deploy | `uninstall` on; read the DANGER note first | [Deploy](/Pipelines/Deploy#danger-uninstall) |
| Fill a new repository's `package/` from an installed app | Onboard | `environment`, `target`, `apps` | [Onboard](/Pipelines/Onboard) |
| Pull installed changes into a repo | App | `importFromNonprod`, `importFromProd`, `importLookups` | [App](/Pipelines/App#import) |
| Compare two environments | Compare | `source`, `target`, `groupPrefix`, `apps` | [Compare](/Pipelines/Compare) |
| Restore app objects to the app's defaults | Repair | `environment`, `target`, `app`, `conf`, `stanzas` | [Repair](/Pipelines/Repair) |
| Disable or enable apps' scheduled searches | Saved searches | `environment`, `target`, `action`, `apps` | [Saved searches](/Pipelines/Saved-searches) |
| Restart a stack that needs it | Restart | `environment`, `target` | [Restart](/Pipelines/Restart) |
| Bulk install indexes, HEC tokens, or apps | Bulk install | `environment`, `type`, `file`, `restart` | [Bulk install](/Pipelines/Bulk) |
| Bulk update indexes, HEC, apps, or permissions | Bulk update | `environment`, `type`, `file`, `restart` | [Bulk update](/Pipelines/Bulk) |
| Bulk delete indexes, HEC tokens, or apps | Bulk delete | `environment`, `type`, `file`, `restart` | [Bulk delete](/Pipelines/Bulk) |
| Check access without changing a stack | Smoke test | none; `target` checks one stack only | [Smoke test](/Pipelines/Smoke-test) |
