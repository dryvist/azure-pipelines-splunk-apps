# App repository

[Home](/Home) > [Getting started](/Getting-started) > App repository

[[_TOC_]]

Steps 5 and 6 cover app repository files and Build Service permissions.

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

4. Add `azure-pipelines.yml` at the repository root.
5. Enter this content:

   ```yaml
   # Keep this file identical across Splunk app repos. Shared logic is in
   # azure-pipelines-splunk-apps. Azure Repos queues PR validation through a
   # main branch Build validation policy and ignores YAML `pr:` triggers.
   parameters:
     - name: importFromNonprod
       displayName: Import this app from nonprod into a new pull request
       type: boolean
       default: false

   trigger:
     batch: true
     branches:
       include: [main]

   resources:
     repositories:
       - repository: tools
         type: git
         # For another project in the org, set the name to
         # <project>/azure-pipelines-splunk-apps.
         name: azure-pipelines-splunk-apps

   extends:
     template: templates/splunk-app.yml@tools
     parameters:
       importFromNonprod: ${{ parameters.importFromNonprod }}
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

## Related

- [App pipeline](/Pipelines/App-pipeline)

---

[< Previous: Environments and ACS](/Getting-started/Environments-and-ACS) |
[Next: App pipeline setup >](/Getting-started/App-pipeline)
