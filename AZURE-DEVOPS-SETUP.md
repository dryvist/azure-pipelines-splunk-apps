# Azure DevOps setup

Follow these steps to set up the shared Splunk app pipeline in an Azure DevOps
project.

## Checklist

| Step | Purpose |
| --- | --- |
| Step 1 | Copy the shared pipeline repository into Azure Repos. |
| Step 2 | Create the package feed and grant publish access. |
| Step 3 | Create the three variable groups. |
| Step 4 | Create deployment environments. |
| Step 5 | Create ACS tokens and grant production export access. |
| Step 6 | Create an app repository and add its pipeline files. |
| Step 7 | Grant the Build Service app repository permissions. |
| Step 8 | Create a pipeline from the existing YAML file. |
| Step 9 | Permit the pipeline to use its resources. |
| Step 10 | Require pipeline validation for pull requests to `main`. |
| Step 11 | Check the first pull request run and its artifacts. |
| Step 12 | Check the first release after merging. |
| Step 13 | Optionally enable production deployment. |
| Step 14 | Publish the repository wiki. |

## Before you start

- Project Administrator access to an Azure DevOps project in `<org>`.
- A Splunk account for AppInspect, with its username and password.
- The Splunk Cloud (Victoria) nonprod and prod stack names.
- Access to create ACS tokens for both stacks. The prod token's account needs
  `export_apps`; `sc_admin` can grant this capability to itself.
- Apps installed this way are private apps. A copy of a Splunkbase app needs
  its own app id in `[id] name`, different from the Splunkbase app id.
- Outbound HTTPS from Azure Pipelines agents to `pypi.org`, `api.splunk.com`,
  `appinspect.splunk.com`, and `admin.splunk.com`. Access to `github.com` is
  needed only for the copy step.

The paths below assume you selected the target project, named `<project>`, in
your Azure DevOps organization, named `<org>`.

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

**You should see:** `azure-pipelines-splunk-apps` on the `main` branch in
**Repos → Files**.

## Step 2 — Create the package feed

**Where:** **Artifacts → Create Feed**

**Do:**

1. Create a project-scoped feed named `splunk-apps`.
2. Open **Feed settings → Permissions**.
3. Add `<project> Build Service (<org>)` with the **Feed Publisher
   (Contributor)** role.

**You should see:** `splunk-apps` in Artifacts and the Build Service listed as
a Feed Publisher (Contributor).

## Step 3 — Create the variable groups

**Where:** **Pipelines → Library → + Variable group**

**Do:**

1. Create each group and variable using the names and secret settings below.
2. Enter the AppInspect username and each stack name. Add the passwords and
   ACS tokens in their matching rows; create the tokens in Step 5.

| Variable group | Variable | Secret? |
| --- | --- | --- |
| `splunk-appinspect` | `SPLUNK_USERNAME` | No |
| `splunk-appinspect` | `SPLUNK_PASSWORD` | Yes |
| `splunk-nonprod` | `SPLUNK_STACK` | No |
| `splunk-nonprod` | `ACS_TOKEN` | Yes |
| `splunk-prod` | `SPLUNK_STACK` | No |
| `splunk-prod` | `ACS_TOKEN` | Yes |

**You should see:** All three groups in Library. Secret values are masked
after they are saved.

## Step 4 — Create deployment environments

**Where:** **Pipelines → Environments → Create environment**

**Do:**

1. Create environments named `splunk-nonprod` and `splunk-prod`.
2. To require approval before production deployment, open `splunk-prod`, then
   **Approvals and checks → Approvals → +** and add the approvers.

**You should see:** Both environments in the environments list. If configured,
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
4. For the prod token's account, open its role in **Settings → Roles** and
   grant the `export_apps` capability. `sc_admin` can grant this capability
   to itself.

**You should see:** One token for each stack, `install_apps` and
`edit_local_apps` on both accounts, and `export_apps` on the prod account.

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
   # Identical in every Splunk app repo. All logic lives in
   # azure-pipelines-splunk-apps. Azure Repos PR runs come from a main branch
   # policy "Build validation"; YAML `pr:` is ignored for Azure Repos.
   trigger:
     batch: true
     branches:
       include: [main]

   resources:
     repositories:
       - repository: tools
         type: git
         # From another project in the org: <project>/azure-pipelines-splunk-apps
         name: azure-pipelines-splunk-apps

   extends:
     template: templates/splunk-app.yml@tools
   ```

4. If the shared repository is in another project, set `name` to
   `<project>/azure-pipelines-splunk-apps`.

**You should see:** The app repository contains `azure-pipelines.yml` and
`package/default/app.conf` on `main`.

## Step 7 — Grant Build Service permissions on the app repository

**Where:** **Project settings → Repositories → `<app-repo>` → Security**

**Do:**

1. Find `<project> Build Service (<org>)`.
2. Allow **Contribute** so the PR version bump can push to the PR source
   branch.
3. Allow **Create tag** so the release stage can push `v<version>`.

**You should see:** Both permissions show **Allow** for the app repository's
Build Service identity.

## Step 8 — Create a pipeline from the YAML file

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select the app repository.
2. Choose **Existing Azure Pipelines YAML file** and select
   `/azure-pipelines.yml`.
3. Save the pipeline with the suggested name or a name that identifies the
   app.

**You should see:** The pipeline page shows the app repository and its
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

**You should see:** The run proceeds past resource authorization and the
pipeline is listed as authorized for the shared repository, groups, and
environments.

## Step 10 — Add the `main` Build validation policy

**Where:** **Repos → Branches → main → Branch policies → Build validation → +**

**Do:**

1. Select the app pipeline.
2. Set the policy to **Automatic** and **Required**, then save it.

Azure Repos uses this branch policy to queue pull request validation. The YAML
`trigger` queues runs for commits to `main`; Azure Repos ignores YAML `pr:`.

**You should see:** The Build validation policy for `main` lists the app
pipeline and requires it to pass.

## Step 11 — Check the first pull request run

**Where:** **Repos → Pull requests → New pull request**; then open its pipeline
run and **Artifacts**.

**Do:**

1. Create a pull request from an app branch into `main`.
2. Confirm `build` packages the app and publishes `dist`.
3. Confirm `appinspect` passes. It reads the `private_victoria` result and
   needs 0 failures, 0 errors and 0 manual checks.
4. Confirm `nonprod` installs the package on the nonprod stack, then
   `proddiff` exports production and creates a diff.
5. Open the run's **Artifacts**. Check `appinspect-report` for the HTML and
   JSON reports when AppInspect produced them. Check `prod-diff` for
   `prod-diff.patch` and the exported `<app-id>-prod.tgz` when present.

The production export can return 404 if the app is not installed there yet.
The stage continues; the patch then shows package files as additions.

**You should see:** Successful `build`, `appinspect`, `nonprod`, and
`proddiff` stages, with `dist`, `appinspect-report`, and `prod-diff` artifacts
on the run.

## Step 12 — Check the first release after merging

**Where:** **Repos → Tags** and **Artifacts → splunk-apps**

**Do:**

1. Merge the validated pull request into `main`.
2. Open the main pipeline run and confirm `build`, `appinspect`, and `release`
   pass.
3. Open **Repos → Tags** and find `v<version>`.
4. Open **Artifacts → splunk-apps** and find the package named with the
   lowercase app id and version from `app.conf`.

**You should see:** The tag points to the release commit and the feed contains
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

**You should see:** A `prod` stage after a successful `main` release. It uses
the prod stack and `splunk-prod` environment. Pull request runs do not deploy
to production.

## Step 14 — Publish the repository wiki

**Where:** **Overview → Wiki → Publish code as wiki**

**Do:**

1. Select repository `azure-pipelines-splunk-apps`.
2. Select branch `main` and folder `/wiki`.
3. Publish the code as the wiki.

**You should see:** The repository pages appear in the Azure DevOps project
wiki, starting at `Home`.

## If a step fails

| Symptom | Fix |
| --- | --- |
| ACS returns 401 or 403 | Check stack, token, `acs` audience, capabilities. |
| Export 404; app absent | Expected; review added files in `prod-diff`. |
| Push denied | Allow Build Service **Contribute** and **Create tag**. |
| AppInspect fails | Check `appinspect-report` and fix its findings. |
| Permission prompt | Select **Permit** for the repo, groups, environments. |
