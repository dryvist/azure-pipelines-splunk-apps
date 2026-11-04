# Appendix: manual app repository and pipeline

Use these steps only if the [Onboard](/Pipelines/Onboard) pipeline cannot run. Onboard does the same work.

## Create the repository and its files

1. Open **Repos → Files**.
2. Select the repository selector.
3. Select **New repository**.
4. Create an Azure Repos Git repository for the app.
5. Add the file `package/default/app.conf`. Enter the app ID and the version:

   ```ini
   [id]
   name = <app-id>
   version = 1.0.0

   [launcher]
   version = 1.0.0
   ```

6. Copy `example/azure-pipelines.yml` from the `azure-pipelines-splunk-apps` repository to `azure-pipelines.yml` at the
   root of the new repository. Keep this file identical across app repositories.
7. Replace `<agent-pool>` with your agent pool name.
8. If the shared repository is in another project, set `name` to `<project>/azure-pipelines-splunk-apps`.

Verify that the repository contains `azure-pipelines.yml` and `package/default/app.conf` on `main`.

## Grant Build Service rights

See [Build Service: App repository](/Setup/Build-service#app-repository).

## Create the app pipeline

Follow [Manual pipelines](/Setup/Manual-pipelines) with these values:

| Field | Value |
| --- | --- |
| Repository | The app repository, not `azure-pipelines-splunk-apps` |
| YAML path | `/azure-pipelines.yml` |
| Pipeline name | A name that identifies the app |

## Permit the pipeline's resources

Run from a branch other than `main`. A `main` run also runs the **Release** stage, which publishes to the feed
and pushes a tag.

1. Select **Repos → Branches**.
2. Select the app repository.
3. Select **New branch**.
4. Select `main` as the base branch.
5. Enter a branch name other than `main`.
6. Create the branch.
7. Select **Pipelines**.
8. Select the app pipeline.
9. Select **Run pipeline**.
10. Select the new branch.
11. Select **Run**.
12. Permit each requested resource. See [Permissions](/Troubleshooting/Permissions).
13. Rerun the pipeline if authorization stopped the run.

## Add the Build validation policy

Follow [Onboard: After onboarding](/Pipelines/Onboard#after-onboarding).

## Check the first pull request and release

1. Select **Repos → Pull requests**.
2. Select **New pull request**.
3. Select the app branch as the source and `main` as the target.
4. Create the pull request.
5. Check the run as described in [App: Check a run](/Pipelines/App#check-a-run).
6. Merge the validated pull request.
7. Check the release as described in [App: Check a release](/Pipelines/App#check-a-release).
