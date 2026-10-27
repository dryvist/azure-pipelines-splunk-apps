# App repository

New app? Use [Onboard an app](Onboard-app.md). The steps below are the manual fallback.

Create the app repository, add its pipeline files, and grant Build Service permissions.

## Step 5: Create an app repository and add its files

**Where:** **Repos → Files → repository selector → New repository**

**Do:**

1. Create an Azure Repos Git repository for the app.
2. Add the file `package/default/app.conf`.
3. Enter the app id and matching version values:

   ```ini
   [id]
   name = <app-id>
   version = 1.0.0

   [launcher]
   version = 1.0.0
   ```

4. Add `azure-pipelines.yml` at the repository root. Keep this file identical across app repos.
5. Enter this content:

   ```yaml
   parameters:
     - name: importFromNonprod
       displayName: Import this app from nonprod into a new pull request
       type: boolean
       default: false
     - name: importFromProd
       displayName: Import this app from prod into a new pull request
       type: boolean
       default: false
     - name: skipLookups
       displayName: When importing, skip lookups (CSV files) and keep the ones on main
       type: boolean
       default: true
     - name: skipLookupBackups
       displayName: When importing, skip Splunk lookup backups (lookups/lookup_file_backups)
       type: boolean
       default: true

   trigger:
     branches:
       include: [main]

   resources:
     repositories:
       - repository: tools
         type: git
         name: azure-pipelines-splunk-apps

   extends:
     template: templates/splunk-app.yml@tools
     parameters:
       importFromNonprod: ${{ parameters.importFromNonprod }}
       importFromProd: ${{ parameters.importFromProd }}
       skipLookups: ${{ parameters.skipLookups }}
       skipLookupBackups: ${{ parameters.skipLookupBackups }}
       pool:
         name: <agent-pool>
   ```

6. Replace `<agent-pool>` with your agent pool name.
7. If the shared repository is in another project, set `name` to
   `<project>/azure-pipelines-splunk-apps`.

**Verify:**

1. Confirm the app repository contains `azure-pipelines.yml` on `main`.
2. Confirm the app repository contains `package/default/app.conf` on `main`.

## Step 6: Grant Build Service permissions on the app repository

**Where:** **Project settings → Repositories → `<app-repo>` → Security**

**Do:**

1. Find `<project> Build Service (<org>)`.
2. Allow **Contribute** so the PR version bump and import branch can be
   pushed to the app repository.
3. Allow **Contribute to pull requests** so the pipeline can create the
   import pull request.
4. Allow **Create tag** so the release stage can push `v<version>`.

**Verify:**

1. Confirm **Contribute** shows **Allow** for the app repository's Build
   Service identity.
2. Confirm **Contribute to pull requests** shows **Allow** for the app
   repository's Build Service identity.
3. Confirm **Create tag** shows **Allow** for the app repository's Build
   Service identity.
