# Azure DevOps setup

Set up the shared Splunk app pipeline in an Azure DevOps project.

## Checklist

| Step | Purpose |
| --- | --- |
| Step 1 | Create the package feed and grant publish access. |
| Step 2 | Create the three variable groups. |
| Step 3 | Create deployment environments. |
| Step 4 | Create ACS tokens and grant export access. |
| Step 5 | Create an app repository and add its pipeline files. |
| Step 6 | Grant the Build Service app repository permissions. |
| Step 7 | Create a pipeline from the existing YAML file. |
| Step 8 | Permit the pipeline to use its resources. |
| Step 9 | Require pipeline validation for pull requests to `main`. |
| Step 10 | Check the first pull request run and its artifacts. |
| Step 11 | Check the first release after merging. |
| Step 12 | Optionally enable production deployment. |
| Step 13 | Publish the repository wiki. |
| Step 14 | Create the nonprod and prod compare pipeline. |

## Before you start

- Project Administrator access to an Azure DevOps project in `<org>`.
- The `azure-pipelines-splunk-apps` repository in that project's Azure
  Repos.
- A Splunk account for AppInspect, with its username and password.
- The Splunk Cloud (Victoria) nonprod and prod stack names.
- Access to create ACS tokens for both stacks. Both token accounts need
  `export_apps`; `sc_admin` can grant this capability to itself.
- Apps installed this way are private apps. A copy of a Splunkbase app needs
  its own app id in `[id] name`, different from the Splunkbase app id.
- Outbound HTTPS from Azure Pipelines agents to `pypi.org`, `api.splunk.com`,
  `appinspect.splunk.com`, `admin.splunk.com`, and `github.com`. Pipelines
  download the ACS CLI from `github.com`.

Select the target project, `<project>`, in the Azure DevOps organization,
`<org>`.

## Step 1: Create the package feed

**Where:** **Artifacts → Create Feed**

**Do:**

1. Select the project scope for the feed.
2. Enter `splunk-apps` as the feed name.
3. Create the feed.
4. Open **Feed settings → Permissions**.
5. Add `<project> Build Service (<org>)`.
6. Set its role to **Feed Publisher (Contributor)**.

**Verify:**

1. Confirm `splunk-apps` appears in Artifacts.
2. Confirm the Build Service is listed as a Feed Publisher (Contributor).

## Step 2: Create the variable groups

**Where:** **Pipelines → Library → + Variable group**

**Do:**

Create the `splunk-appinspect` group:

1. Select **+ Variable group**.
2. Type `splunk-appinspect` as the group name.
3. Type `Splunk.com account for AppInspect validation and ACS installs` as
   the description.
4. Add a variable.
5. Type `SPLUNK_USERNAME` as the variable name.
6. Type the username of a splunk.com account as its value.
7. Set its lock icon off. Do not lock `SPLUNK_USERNAME`; locked variables
   are not passed to scripts unless mapped.
8. Add a variable.
9. Type `SPLUNK_PASSWORD` as the variable name.
10. Type the password of the same splunk.com account as its value.
11. Set its lock icon on.

`SPLUNK_USERNAME` is sourced from the account used to sign in at splunk.com
and Splunkbase. `appinspect` uses it; `nonprod` and `prod` send its AppInspect
token to ACS as proof of validation. `SPLUNK_PASSWORD` is used by the same
stages as `SPLUNK_USERNAME`.

Create the `splunk-nonprod` group:

1. Select **+ Variable group**.
2. Type `splunk-nonprod` as the group name.
3. Type `Nonprod Splunk Cloud stack for pull request installs` as the
description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the nonprod stack name as its value. It is the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
7. Set its lock icon off. Do not lock `SPLUNK_STACK`; locked variables are
    not passed to scripts unless mapped.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until Step 4.
11. Set its lock icon on.

`SPLUNK_STACK` is used by `nonprod`. The `ACS_TOKEN` value is a Splunk Cloud
authentication token with audience `acs`, sourced from Splunk Web on the
nonprod stack in Step 4 and used by `nonprod`.

Create the `splunk-prod` group:

1. Select **+ Variable group**.
2. Type `splunk-prod` as the group name.
3. Type `Production Splunk Cloud stack for export, diff and deploy` as the
description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the production stack name as its value. It is the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
7. Set its lock icon off. Do not lock `SPLUNK_STACK`; locked variables are
    not passed to scripts unless mapped.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until Step 4.
11. Set its lock icon on.

The prod `SPLUNK_STACK` is used by `proddiff` and `prod`. The prod `ACS_TOKEN`
value is a Splunk Cloud authentication token with audience `acs`; its account
needs `export_apps`, `install_apps` and `edit_local_apps`. The token is sourced
from Splunk Web on the production stack in Step 4 and used by `proddiff` and
`prod`.

**Verify:**

1. Confirm the group names are exactly `splunk-appinspect`,
   `splunk-nonprod`, and `splunk-prod`, with hyphens, typed exactly.
2. Confirm all three groups appear in Library.
3. Confirm secret values are masked after they are saved.

## Step 3: Create deployment environments

**Where:** **Pipelines → Environments**

**Do:**

1. Select **Create environment**.
2. Enter `splunk-nonprod` as the environment name.
3. Create the environment.
4. Select **Create environment**.
5. Enter `splunk-prod` as the environment name.
6. Create the environment.

To require approval before production deployment:

1. Open `splunk-prod`.
2. Go to **Approvals and checks → Approvals → +**.
3. Add the approvers.

**Verify:**

1. Confirm `splunk-nonprod` appears in the environments list.
2. Confirm `splunk-prod` appears in the environments list.
3. If configured, confirm the prod environment shows its approval check.

## Step 4: Create ACS tokens and grant export access

**Where:** In Splunk Web, use **Settings → Tokens** for each stack and
**Settings → Roles** for roles. To enter token values, use
**Pipelines → Library → `<group>`**.

**Do:**

1. In Splunk Web for the nonprod stack, go to **Settings → Tokens**.
2. Create an ACS token for the nonprod stack.
3. Set its audience to `acs`.
4. In Splunk Web for the prod stack, go to **Settings → Tokens**.
5. Create an ACS token for the prod stack.
6. Set its audience to `acs`.
7. Go to **Pipelines → Library → `splunk-nonprod`**.
8. Enter the nonprod token as the `ACS_TOKEN` value.
9. Go to **Pipelines → Library → `splunk-prod`**.
10. Enter the prod token as the `ACS_TOKEN` value.
11. Go to **Settings → Roles**.
12. Open the role for the nonprod token account.
13. Confirm that the nonprod token account has `install_apps`.
14. Confirm that the nonprod token account has `edit_local_apps`.
15. Grant the nonprod token account the `export_apps` capability.
16. Go to **Settings → Roles**.
17. Open the role for the prod token account.
18. Confirm that the prod token account has `install_apps`.
19. Confirm that the prod token account has `edit_local_apps`.
20. Grant the prod token account the `export_apps` capability.

`sc_admin` can grant the `export_apps` capability to itself.

**Verify:**

1. Confirm one token exists for the nonprod stack.
2. Confirm one token exists for the prod stack.
3. Confirm the nonprod account has `install_apps`.
4. Confirm the nonprod account has `edit_local_apps`.
5. Confirm the nonprod account has `export_apps`.
6. Confirm the prod account has `install_apps`.
7. Confirm the prod account has `edit_local_apps`.
8. Confirm the prod account has `export_apps`.

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
   ```

6. If the shared repository is in another project, set `name` to
   `<project>/azure-pipelines-splunk-apps`.

**Verify:**

1. Confirm the app repository contains `azure-pipelines.yml` on `main`.
2. Confirm the app repository contains `package/default/app.conf` on `main`.

## Step 6: Grant Build Service permissions on the app repository

**Where:** **Project settings → Repositories → `<app-repo>` → Security**

**Do:**

1. Find `<project> Build Service (<org>)`.
2. Allow **Contribute** so the PR version bump can push to the PR source
   branch.
3. Allow **Create tag** so the release stage can push `v<version>`.

**Verify:**

1. Confirm **Contribute** shows **Allow** for the app repository's Build
   Service identity.
2. Confirm **Create tag** shows **Allow** for the app repository's Build
   Service identity.

## Step 7: Create a pipeline from the YAML file

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select the app repository, not `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/azure-pipelines.yml`.
4. If using a custom name, enter a name that identifies the app.
5. Save the pipeline.

**Verify:**

1. Confirm the pipeline page shows the app repository.
2. Confirm the pipeline page shows its `azure-pipelines.yml` file.

## Step 8: Permit the pipeline to use its resources

**Where:** **Repos → Branches** and **Pipelines → Pipelines → `<pipeline>`**

**Do:**

Run from a branch other than `main`: a `main` run also runs the `release` stage,
which publishes to the feed and pushes a tag.

1. Go to **Repos → Branches → repository selector**.
2. Select the app repository.
3. Go to **Repos → Branches → New branch**.
4. Select `main` as the branch to base the new branch on.
5. Enter a branch name other than `main`.
6. Create the branch.
7. Go to **Pipelines → Pipelines → `<pipeline>`**.
8. Select **Run pipeline**.
9. Select the new branch.
10. Select **Run**.

When Azure DevOps reports that a resource needs authorization:

1. Select **Permit** for `azure-pipelines-splunk-apps`.
2. Select **Permit** for `splunk-appinspect`.
3. Select **Permit** for `splunk-nonprod`.
4. Select **Permit** for `splunk-prod`.
5. Select **Permit** for the `splunk-nonprod` environment.
6. Select **Permit** for the `splunk-prod` environment.

If no Permit banner appears, authorize each variable group:

1. Go to **Pipelines → Library → `splunk-appinspect` → Pipeline
    permissions**.
2. Select **+**.
3. Select the pipeline.
4. Go to **Pipelines → Library → `splunk-nonprod` → Pipeline
    permissions**.
5. Select **+**.
6. Select the pipeline.
7. Go to **Pipelines → Library → `splunk-prod` → Pipeline permissions**.
8. Select **+**.
9. Select the pipeline.

If no Permit banner appears, authorize each environment:

1. Go to **Pipelines → Environments → `splunk-nonprod` → ⋮ → Security →
    Pipeline permissions**.
2. Select **+**.
3. Select the pipeline.
4. Go to **Pipelines → Environments → `splunk-prod` → ⋮ → Security →
    Pipeline permissions**.
5. Select **+**.
6. Select the pipeline.

**Verify:**

1. Confirm the run proceeds past resource authorization.
2. Confirm the shared repository is authorized for the pipeline.
3. Confirm `splunk-appinspect` is authorized for the pipeline.
4. Confirm `splunk-nonprod` is authorized for the pipeline.
5. Confirm `splunk-prod` is authorized for the pipeline.
6. Confirm the `splunk-nonprod` environment is authorized for the pipeline.
7. Confirm the `splunk-prod` environment is authorized for the pipeline.

## Step 9: Add the `main` Build validation policy

**Where:** **Repos → Branches → main → Branch policies → Build validation → +**

**Do:**

1. Select the app pipeline.
2. Set the policy to **Automatic**.
3. Set the policy to **Required**.
4. Save the policy.

Azure Repos uses this branch policy to queue pull request validation. The YAML
`trigger` queues runs for commits to `main`; Azure Repos ignores YAML `pr:`.

**Verify:**

1. Confirm the Build validation policy for `main` lists the app pipeline.
2. Confirm the policy requires the app pipeline to pass.

## Step 10: Check the first pull request run

**Where:** **Repos → Pull requests → New pull request**; then open its pipeline
run and **Artifacts**.

**Do:**

1. Select the app branch as the source branch.
2. Select `main` as the target branch.
3. Create the pull request.
4. Confirm `build` packages the app.
5. Confirm `build` publishes `dist`.
6. Confirm `appinspect` reads the `private_victoria` results.
7. Confirm `appinspect` reads the `future` results.
8. Confirm the failure count is 0.
9. Confirm the error count is 0.
10. Confirm the manual checks count is 0.
11. Confirm `appinspect` passes.
12. If `future_failure` is above 0, confirm the run shows a warning.
13. Confirm `nonprod` installs the package on the nonprod stack.
14. Confirm `proddiff` exports production.
15. Confirm `proddiff` creates a diff.
16. Open the `appinspect` job's **Show AppInspect JSON report** step.
17. Confirm that step prints the full JSON report.
18. Open the **Show AppInspect HTML report link** step.
19. Select the link.
20. Open `appinspect-report-<attempt>` with the highest attempt number.
21. Download `appinspect-report.html`.
22. Open `appinspect-report.html` in a browser.
23. Open `prod-diff-<attempt>` with the highest attempt number.
24. Confirm it contains `<app-id>.patch`.
25. Confirm it contains `<app-id>-summary.md`.

Each job attempt publishes its own artifact, so a rerun keeps earlier
reports and adds a new one with the next attempt number.

If the app is not installed in production yet, the export log shows
`NOT INSTALLED <app-id>`. The stage continues, and the summary lists every
package file as added.

**Verify:**

1. Confirm `build` succeeds.
2. Confirm `appinspect` succeeds.
3. Confirm `nonprod` succeeds.
4. Confirm `proddiff` succeeds.
5. Confirm the run has a `dist` artifact.
6. Confirm the run has an `appinspect-report-1` artifact.
7. Confirm the run has a `prod-diff-1` artifact.

## Step 11: Check the first release after merging

**Where:** **Repos → Tags** and **Artifacts → splunk-apps**

**Do:**

1. Merge the validated pull request into `main`.
2. Open the main pipeline run.
3. Confirm `build` passes.
4. Confirm `appinspect` passes.
5. Confirm `release` passes.
6. Go to **Repos → Tags**.
7. Find `v<version>`.
8. Go to **Artifacts → splunk-apps**.
9. Find the package named with the lowercase app id and version from
   `app.conf`.

**Verify:**

1. Confirm the tag points to the release commit.
2. Confirm the feed contains the matching Universal Package version.

## Step 12: Optionally enable production deployment

**Where:** The app repository's root `azure-pipelines.yml` file.

**Do:**

1. Add `prod: true` under `extends`:

   ```yaml
   extends:
     template: templates/splunk-app.yml@tools
     parameters:
       prod: true
   ```

2. Commit the change to `main`.
3. Confirm the `splunk-prod` environment has an approval check if production
   approval is required.

**Verify:**

1. Confirm a `prod` stage follows a successful `main` release.
2. Confirm the `prod` stage uses the prod stack.
3. Confirm the `prod` stage uses the `splunk-prod` environment.
4. Confirm pull request runs do not deploy to production.

## Step 13: Publish the repository wiki

**Where:** **Overview → Wiki → Publish code as wiki**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Select branch `main`.
3. Select folder `/wiki`.
4. Publish the code as the wiki.

**Verify:**

1. Confirm the repository pages appear in the Azure DevOps project wiki.
2. Confirm the wiki starts at `Home`.

## Step 14: Create the compare pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/compare/azure-pipelines.yml`.
4. Enter `compare-nonprod-prod` as the pipeline name.
5. Save the pipeline.
6. Select **Run pipeline**.
7. In **App IDs, separated by spaces**, enter the app ids to compare, for
   example `my_app other_app`. Use the app folder names from `[id] name`, not
   the display labels.
8. Select **Run**.
9. When asked, select **Permit** for the `splunk-nonprod` group.
10. When asked, select **Permit** for the `splunk-prod` group.

**Verify:**

1. Confirm the `nonprod` job succeeds.
2. Confirm the `prod` job succeeds.
3. Confirm the `compare` job succeeds.
4. Confirm the `compare` artifact holds `<app-id>.patch` for each app.
5. Confirm the `compare` artifact holds `<app-id>-summary.md` for each app.
6. Confirm the `compare` job log prints each summary.

## If a step fails

| Symptom | Fix |
| --- | --- |
| ACS returns 401 or 403 | Check stack, token, `acs` audience, capabilities. |
| `NOT INSTALLED <app-id>` | Expected for a new app; files show as added. |
| Push denied | Allow Build Service **Contribute** and **Create tag**. |
| AppInspect fails | Check `appinspect-report-<attempt>` and fix its findings. |
| Permission prompt | Select **Permit** for the repo, groups, environments. |
