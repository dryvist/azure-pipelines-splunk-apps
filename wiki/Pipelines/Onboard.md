# Onboard pipeline

The Onboard pipeline creates a repository and an app pipeline for each app that is installed on a stack but
has no repository. Both are named exactly the app ID.

Before the first run, grant the one-time permissions in [Build Service](/Setup/Build-service). Create the
pipeline from [Manual pipelines](/Setup/Manual-pipelines), with YAML path `/onboard/azure-pipelines.yml`.

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to export the app from. Uses `splunk-<environment>`. |
| `apps` | App IDs separated by `;` | none | Apps to export and onboard. Each app runs in its own job. |
| `permissions` | on, off | on | Grants the project Build Service Contribute, Contribute to pull requests, and Create tag. |

## Run it

1. Open the Onboard pipeline and select **Run pipeline**.
2. Select `nonprod` or `prod` for **environment**.
3. Enter the app IDs for **App IDs**, such as `my_app;other_app`.
4. Keep **Grant app repository permissions** on. To grant them by hand, turn it off and follow
   [Build Service: App repository](/Setup/Build-service#app-repository).
5. Select **Run**.
6. Permit each requested resource. See [Permissions](/Troubleshooting/Permissions).

Each job exports its app, creates the repository, and writes the export to `package/`. It copies the app's
`azure-pipelines.yml`, pushes the initial commit to `main`, and creates the app pipeline.

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

If you turned off permissions, grant them first. See
[Build Service: App repository](/Setup/Build-service#app-repository).
