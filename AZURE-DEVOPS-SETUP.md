# Azure DevOps setup

Set up the shared Splunk app pipeline in an Azure DevOps project.

## Checklist

| Step | Purpose |
| --- | --- |
| Step 1 | Copy the shared pipeline repository into Azure Repos. |
| Step 2 | Create the package feed and grant publish access. |
| Step 3 | Create the three variable groups. |
| Step 4 | Create deployment environments. |
| Step 5 | Create ACS tokens and grant export access. |
| Step 6 | Create an app repository and add its pipeline files. |
| Step 7 | Grant the Build Service app repository permissions. |
| Step 8 | Create a pipeline from the existing YAML file. |
| Step 9 | Permit the pipeline to use its resources. |
| Step 10 | Require pipeline validation for pull requests to `main`. |
| Step 11 | Check the first pull request run and its artifacts. |
| Step 12 | Check the first release after merging. |
| Step 13 | Optionally enable production deployment. |
| Step 14 | Publish the repository wiki. |
| Step 15 | Create the nonprod and prod compare pipeline. |

## Before you start

- Project Administrator access to an Azure DevOps project in `<org>`.
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

## Step 1 — Copy the shared pipeline repository

**Where:** **Repos → Files → repository selector**

**Do:**

Use **either** option A or option B.

Option A, import in the browser:

1. Choose **Import repository**.
2. Source URL: `https://github.com/dryvist/azure-pipelines-splunk-apps.git`
3. Name: `azure-pipelines-splunk-apps`

Option B, Git commands from any machine that reaches `github.com` and
`dev.azure.com`. Replace `<org>` and `<project>` with your Azure DevOps names:

```sh
git clone https://github.com/dryvist/azure-pipelines-splunk-apps.git
cd azure-pipelines-splunk-apps
git push \
  https://dev.azure.com/<org>/<project>/_git/azure-pipelines-splunk-apps \
  main --tags
```

Git Credential Manager opens a browser sign-in. Or use a personal access token
with **Code (Read & write)** as the password.

To update later, run these inside the `azure-pipelines-splunk-apps` folder:

```sh
git pull
git push \
  https://dev.azure.com/<org>/<project>/_git/azure-pipelines-splunk-apps \
  main --tags
```

**Verify:** `azure-pipelines-splunk-apps` is on the `main` branch in
**Repos → Files**.

## Step 2 — Create the package feed

**Where:** **Artifacts → Create Feed**

**Do:**

1. Create a project-scoped feed named `splunk-apps`.
2. Open **Feed settings → Permissions**.
3. Add `<project> Build Service (<org>)` with the **Feed Publisher
   (Contributor)** role.

**Verify:** `splunk-apps` appears in Artifacts. The Build Service is listed as
a Feed Publisher (Contributor).

## Step 3 — Create the variable groups

**Where:** **Pipelines → Library → + Variable group**

**Do:**

1. Create the three groups below. Enter each **Description** in the group's
   Description field.
2. Add each variable. Select the lock icon for every variable marked
   **Secret: Yes**.
3. Leave `ACS_TOKEN` empty until Step 5 creates the tokens.

### Group `splunk-appinspect`

Description: `Splunk.com account for AppInspect validation and ACS installs`

- `SPLUNK_USERNAME` (Secret: No)
  - Value: user name of a splunk.com account.
  - Source: the account used to sign in at splunk.com and Splunkbase.
  - Used by: `appinspect`; `nonprod` and `prod` send its AppInspect token to
    ACS as proof of validation.
- `SPLUNK_PASSWORD` (Secret: Yes)
  - Value: password of the same splunk.com account.
  - Used by: the same stages as `SPLUNK_USERNAME`.

### Group `splunk-nonprod`

Description: `Nonprod Splunk Cloud stack for pull request installs`

- `SPLUNK_STACK` (Secret: No)
  - Value: the stack name, the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
  - Used by: `nonprod`.
- `ACS_TOKEN` (Secret: Yes)
  - Value: a Splunk Cloud authentication token with audience `acs`.
  - Source: Splunk Web on the nonprod stack, Step 5.
  - Used by: `nonprod`.

### Group `splunk-prod`

Description: `Production Splunk Cloud stack for export, diff and deploy`

- `SPLUNK_STACK` (Secret: No)
  - Value: the production stack name, the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
  - Used by: `proddiff` and `prod`.
- `ACS_TOKEN` (Secret: Yes)
  - Value: a Splunk Cloud authentication token with audience `acs`. The
    token's account needs `export_apps`, `install_apps` and
    `edit_local_apps`.
  - Source: Splunk Web on the production stack, Step 5.
  - Used by: `proddiff` and `prod`.

**Verify:** All three groups appear in Library. Secret values are masked
after they are saved.

## Step 4 — Create deployment environments

**Where:** **Pipelines → Environments → Create environment**

**Do:**

1. Create environments named `splunk-nonprod` and `splunk-prod`.
2. To require approval before production deployment, open `splunk-prod`, then
   **Approvals and checks → Approvals → +** and add the approvers.

**Verify:** Both environments appear in the environments list. If configured,
the prod environment shows its approval check.

## Step 5 — Create ACS tokens and grant export access

**Where:** In Splunk Web for each stack, use **Settings → Tokens**. For roles,
use **Settings → Roles**.

**Do:**

1. Create an ACS token for the nonprod stack and one for the prod stack. Use
   the `acs` audience.
2. Put each token in that stack's `ACS_TOKEN` variable in its matching group.
   Keep both variables marked secret.
3. Both token accounts need the `install_apps` and `edit_local_apps`
   capabilities to install apps.
4. For both token accounts, open the role in **Settings → Roles** and grant
   the `export_apps` capability. `sc_admin` can grant this capability to
   itself.

**Verify:** One token exists for each stack. Both accounts have
`install_apps`, `edit_local_apps`, and `export_apps`.

## Step 6 — Create an app repository and add its files

**Where:** **Repos → Files → repository selector → New repository**

**Do:**

1. Create an Azure Repos Git repository for the app.
2. Add `package/default/app.conf` with the app id and matching version values:

   ```ini
   [id]
   name = <app-id>
   version = 1.0.0

   [launcher]
   version = 1.0.0
   ```

3. Add `azure-pipelines.yml` at the repository root with this content:

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

4. If the shared repository is in another project, set `name` to
   `<project>/azure-pipelines-splunk-apps`.

**Verify:** The app repository contains `azure-pipelines.yml` and
`package/default/app.conf` on `main`.

## Step 7 — Grant Build Service permissions on the app repository

**Where:** **Project settings → Repositories → `<app-repo>` → Security**

**Do:**

1. Find `<project> Build Service (<org>)`.
2. Allow **Contribute** so the PR version bump can push to the PR source
   branch.
3. Allow **Create tag** so the release stage can push `v<version>`.

**Verify:** Both permissions show **Allow** for the app repository's
Build Service identity.

## Step 8 — Create a pipeline from the YAML file

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select the app repository.
2. Choose **Existing Azure Pipelines YAML file** and select
   `/azure-pipelines.yml`.
3. Save the pipeline with the suggested name or a name that identifies the
   app.

**Verify:** The pipeline page shows the app repository and its
`azure-pipelines.yml` file.

## Step 9 — Permit the pipeline to use its resources

**Where:** **Pipelines → Pipelines → `<pipeline>`**

**Do:**

1. Start a run from `main` if pipeline creation did not start one.
2. When Azure DevOps reports that a resource needs authorization, select
   **Permit** for `azure-pipelines-splunk-apps`, the three variable groups,
   and both environments.
3. If needed, open each group at **Pipelines → Library → `<group>` → Pipeline
   permissions** and authorize this pipeline.

**Verify:** The run proceeds past resource authorization and the
pipeline is listed as authorized for the shared repository, groups, and
environments.

## Step 10 — Add the `main` Build validation policy

**Where:** **Repos → Branches → main → Branch policies → Build validation → +**

**Do:**

1. Select the app pipeline.
2. Set the policy to **Automatic** and **Required**, then save it.

Azure Repos uses this branch policy to queue pull request validation. The YAML
`trigger` queues runs for commits to `main`; Azure Repos ignores YAML `pr:`.

**Verify:** The Build validation policy for `main` lists the app
pipeline and requires it to pass.

## Step 11 — Check the first pull request run

**Where:** **Repos → Pull requests → New pull request**; then open its pipeline
run and **Artifacts**.

**Do:**

1. Create a pull request from an app branch into `main`.
2. Confirm `build` packages the app and publishes `dist`.
3. Confirm `appinspect` passes. It reads the `private_victoria` and `future`
   results and needs 0 failures, 0 errors and 0 manual checks. A
   `future_failure` count above 0 shows as a warning on the run.
4. Confirm `nonprod` installs the package on the nonprod stack, then
   `proddiff` exports production and creates a diff.
5. Open the run's **Artifacts**. Check `appinspect-report` for the HTML and
   JSON reports when AppInspect produced them. Check `prod-diff` for
   `<app-id>.patch` and `<app-id>-summary.md`.

If the app is not installed in production yet, the export log shows
`NOT INSTALLED <app-id>`. The stage continues, and the summary lists every
package file as added.

**Verify:** `build`, `appinspect`, `nonprod`, and `proddiff` succeed, with
`dist`, `appinspect-report`, and `prod-diff` artifacts on the run.

## Step 12 — Check the first release after merging

**Where:** **Repos → Tags** and **Artifacts → splunk-apps**

**Do:**

1. Merge the validated pull request into `main`.
2. Open the main pipeline run and confirm `build`, `appinspect`, and `release`
   pass.
3. Open **Repos → Tags** and find `v<version>`.
4. Open **Artifacts → splunk-apps** and find the package named with the
   lowercase app id and version from `app.conf`.

**Verify:** The tag points to the release commit and the feed contains
the matching Universal Package version.

## Step 13 — Optionally enable production deployment

**Where:** The app repository's root `azure-pipelines.yml` file.

**Do:**

1. Add `prod: true` under `extends`:

   ```yaml
   extends:
     template: templates/splunk-app.yml@tools
     parameters:
       prod: true
   ```

2. Commit the change to `main`. Confirm the `splunk-prod` environment has an
   approval check if production approval is required.

**Verify:** A `prod` stage follows a successful `main` release. It uses
the prod stack and `splunk-prod` environment. Pull request runs do not deploy
to production.

## Step 14 — Publish the repository wiki

**Where:** **Overview → Wiki → Publish code as wiki**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Select branch `main` and folder `/wiki`.
3. Publish the code as the wiki.

**Verify:** The repository pages appear in the Azure DevOps project
wiki, starting at `Home`.

## Step 15 — Create the compare pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file** and select
   `/compare/azure-pipelines.yml`.
3. Save the pipeline as `compare-nonprod-prod`.
4. Select **Run pipeline**. In **App IDs, separated by spaces**, enter the
   app ids to compare, for example `my_app other_app`. Use the app folder
   names from `[id] name`, not the display labels.
5. Select **Permit** for the `splunk-nonprod` and `splunk-prod` groups when
   asked.

**Verify:** The `nonprod`, `prod`, and `compare` jobs succeed. The `compare`
artifact holds `<app-id>.patch` and `<app-id>-summary.md` for each app. The
`compare` job log prints each summary.

## If a step fails

| Symptom | Fix |
| --- | --- |
| ACS returns 401 or 403 | Check stack, token, `acs` audience, capabilities. |
| `NOT INSTALLED <app-id>` | Expected for a new app; files show as added. |
| Push denied | Allow Build Service **Contribute** and **Create tag**. |
| AppInspect fails | Check `appinspect-report` and fix its findings. |
| Permission prompt | Select **Permit** for the repo, groups, environments. |
