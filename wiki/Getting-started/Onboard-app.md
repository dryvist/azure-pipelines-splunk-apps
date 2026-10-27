# Onboard an installed app

[Home](/Home) > [Getting started](/Getting-started) > Onboard an installed app

[[_TOC_]]

Use this page to create a repository and pipeline for an app that is installed but has no repository.

## Preconditions

1. Give the Build Service **Administer** or **User** on the variable groups and environments, and **Administer** on the `tools` repository.

## One-time project setup

1. Open the project.
2. Select **Project settings**.
3. Select **Repositories**.
4. Select **All Repositories**.
5. Select **Security**.
6. Select `<project> Build Service (<organization>)`.
7. Set **Create repository** to **Allow**.
8. Select **Pipelines**.
9. Select **More actions**.
10. Select **Manage security**.
11. Select `<project> Build Service (<organization>)`.
12. Set **Create build pipeline** to **Allow**.

## Create the Onboard pipeline

1. Select **Pipelines**.
2. Select **New pipeline**.
3. Select **Azure Repos Git**.
4. Select the `azure-pipelines-splunk-apps` repository.
5. Select **Existing Azure Pipelines YAML file**.
6. Select `main` as the branch.
7. Select `/onboard/azure-pipelines.yml`.
8. Select **Continue**.
9. Open the menu beside **Run**.
10. Select **Save**.

## Run it

1. Open the pipeline you saved above.
2. Select **Run pipeline**.
3. Select `nonprod` or `prod` for **environment**.
4. Enter the app id for **app**.
5. Enter a **repository** name, or leave it empty to use the app id.
6. Keep **Grant app repository permissions** on, or turn it off to grant permissions by hand.
7. Select **Run**.

## After onboarding

1. Open `azure-pipelines.yml` in the new repository.
2. Replace `<agent-pool>` with an agent pool in the project, or remove the `pool` block to use `ubuntu-latest`.
3. Commit the change to `main`.
4. If the run prompts you to authorize `<agent-pool>`, select **Permit**. This is needed only when the pool is not open to all pipelines.

That commit starts the app pipeline on `main`. The run executes Build, AppInspect, and Release, as for any app.

If you turned off permissions, grant them first. See [App repository](/Getting-started/App-repository).
