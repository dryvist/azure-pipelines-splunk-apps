# Appendix: manual app repository and pipeline

**Replaced by the Onboard pipeline. Use only if Onboard cannot run.**

One time. Done at project setup; you should not need this again.

Use these steps to create an app repository and its pipeline by hand. The [Onboard](/Pipelines/Onboard) pipeline
does the same work.

## Create the repository and its files

1. Open **Repos → Files**. Select the repository selector, then **New repository**. Create an Azure Repos Git
   repository for the app.
2. Add the file `package/default/app.conf`. Enter the app ID and the version:

   ```ini
   [id]
   name = <app-id>
   version = 1.0.0

   [launcher]
   version = 1.0.0
   ```

3. Add `azure-pipelines.yml` at the repository root. Keep this file identical across app repositories. Enter this
   content, and replace `<agent-pool>` with your agent pool name:

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

4. If the shared repository is in another project, set `name` to `<project>/azure-pipelines-splunk-apps`.

Verify that the repository contains `azure-pipelines.yml` and `package/default/app.conf` on `main`.

## Grant Build Service rights

See [Build Service: App repository](/Setup/Build-service#app-repository).

## Create the app pipeline

1. Open **Pipelines**. Select **New pipeline**, then **Azure Repos Git**.
2. Select the app repository. Do not select `azure-pipelines-splunk-apps`.
3. Select **Existing Azure Pipelines YAML file**, then `/azure-pipelines.yml`.
4. If you use a custom name, enter a name that identifies the app.
5. Select **Save**. The pipeline page shows the app repository and `azure-pipelines.yml`.

## Permit the pipeline's resources

Run from a branch other than `main`. A `main` run also runs the **Release** stage, which publishes to the feed
and pushes a tag.

1. Select **Repos → Branches**, select the app repository, then select **New branch**.
2. Select `main` as the base branch. Enter a branch name other than `main`, then create the branch.
3. Select **Pipelines**, select the app pipeline, then select **Run pipeline**.
4. Select the new branch, then select **Run**.
5. Permit each requested resource. See [Permissions](/Troubleshooting/Permissions). Rerun the pipeline if
   authorization stopped the run.

## Add the Build validation policy

Follow [Onboard: After onboarding](/Pipelines/Onboard#after-onboarding), step 5.

## Check the first pull request and release

1. Select **Repos → Pull requests**, then **New pull request**. Select the app branch as the source and `main`
   as the target. Create the pull request.
2. Check the run as described in [App: Check a run](/Pipelines/App#check-a-run).
3. Merge the validated pull request. Then check the release as described in
   [App: Check a release](/Pipelines/App#check-a-release).
