# Which pipeline?

Find your task in the first column. Set the parameters in the third column. Then open the page in the last column.

| Task | Pipeline | Parameters to set | Page |
| --- | --- | --- | --- |
| Release a change to one app | App | Open a pull request to `main`, merge it, then approve the prod install | [App](/Pipelines/App) |
| Deploy one app to nonprod or prod | Deploy | `environment`, `apps` (one ID), `compare`, `install`, `restart` | [Deploy](/Pipelines/Deploy) |
| Deploy several apps | Deploy | `apps` as IDs separated by `;`, such as `app_one;app_two`, plus the options above | [Deploy](/Pipelines/Deploy) |
| Deploy to prod with compare review | Deploy | `environment` = `prod`; approve each compare, then the install | [Deploy](/Pipelines/Deploy#deploy-to-prod) |
| Replace apps (DANGER: deletes lookups) | Deploy | `uninstall` on; read the DANGER note first | [Deploy](/Pipelines/Deploy#danger-uninstall) |
| Fill a new empty repository from an installed app | Onboard | `environment`, `target`, `apps` | [Onboard](/Pipelines/Onboard) |
| Pull installed changes into a repo | App | `importFromNonprod`, `importFromProd`, `skipLookups` | [App](/Pipelines/App#import) |
| Compare two environments | Compare | `source`, `target`, `groupPrefix`, `apps` | [Compare](/Pipelines/Compare) |
| Restore app objects to the app's defaults | Repair | `environment`, `target`, `app`, `conf`, `stanzas` | [Repair](/Pipelines/Repair) |
| Restart a stack that needs it | Restart | `environment`, `target` | [Restart](/Pipelines/Restart) |
| Bulk install indexes, HEC tokens, or apps | Bulk install | `environment`, `type`, `file`, `restart` | [Bulk install](/Pipelines/Bulk-Install) |
| Bulk update indexes, HEC, apps, or permissions | Bulk update | `environment`, `type`, `file`, `restart` | [Bulk update](/Pipelines/Bulk-Update) |
| Bulk delete indexes, HEC tokens, or apps | Bulk delete | `environment`, `type`, `file`, `restart` | [Bulk delete](/Pipelines/Bulk-Delete) |
| Check access without changing a stack | Smoke test | none; `target` checks one stack only | [Smoke test](/Pipelines/Smoke-test) |
