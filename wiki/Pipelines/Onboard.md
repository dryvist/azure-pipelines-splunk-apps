# Onboard pipeline

The Onboard pipeline fills a new, empty repository from an app installed on a stack. It then creates the app
pipeline. The repository and the pipeline are named exactly the app ID.

Onboard takes private apps only. Through ACS, it stops when the app is not installed on the search head or
is a Splunkbase app.

Before the first run, grant the one-time permissions in [Build Service](/Setup/Build-service). Create the
pipeline from [Manual pipelines](/Setup/Manual-pipelines), with YAML path `/onboard/azure-pipelines.yml`.

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to export the app from. |
| `target` | `splunk-itsi`, `splunk` | `splunk-itsi` | Search head to export from. Uses `<target>-<environment>`. |
| `apps` | App IDs separated by `;` | none | Apps to export and onboard. Each app runs in its own job. |

## Create each repository

Do these steps for each app before you run Onboard.

1. Open **Repos**.
2. Open the repository list at the top and select **New repository**.
3. Keep **Repository type** as **Git**.
4. Enter the app ID as **Repository name**. Match its case exactly.
5. Clear **Add a README**. Keep **Add a .gitignore** as **None**. The repository must be empty.
6. Select **Create**.
7. Grant the rights in [Build Service: App repository](/Setup/Build-service#app-repository).

## Run it

1. Open the Onboard pipeline and select **Run pipeline**.
2. Select `nonprod` or `prod` for **environment**.
3. Keep `splunk-itsi` for **target**, or select `splunk` for the main search head.
4. Enter the app IDs for **App IDs**, such as `my_app;other_app`.
5. Select **Run**.
6. Permit each requested resource, including each new repository. See [Permissions](/Troubleshooting/Permissions).

Each job exports its app and writes the export to `package/`. It copies the app's `azure-pipelines.yml`, pushes
the initial commit to `main`, and creates the app pipeline.

## After onboarding

Do these steps once for each new app repository.

1. Open `azure-pipelines.yml` in the new repository.
2. Replace `<agent-pool>` with an agent pool in the project. Or remove the `pool` block to use `ubuntu-latest`.
3. Commit the change to `main`. The commit starts the app pipeline on `main`. That run goes through every
   stage described in [App](/Pipelines/App).
4. If the run asks you to authorize `<agent-pool>`, select **Permit**. This is needed only when the pool is
   not open to all pipelines.
5. Add the Build validation policy on `main`. Onboard does not add it. Open **Repos → Branches**, select
   `main`, and open **Branch policies**. Add a **Build validation** policy, select the app pipeline, set the
   policy to **Automatic** and **Required**, and save.
