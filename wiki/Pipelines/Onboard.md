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

## Create the repositories

Create one empty repository per app before you run Onboard. Each repository is named exactly the app ID.

First, grant the Build Service rights once for all repositories. See
[Build Service: App repository](/Setup/Build-service#app-repository).

### Many at once

Use this for several apps. It needs Python 3 and a personal access token (PAT).

1. In Azure DevOps, open **User settings** (top right), then **Personal access tokens**.
2. Select **New Token**. Set **Expiration** to 1 day.
3. Under **Scopes**, select **Custom defined**, then **Code: Read, write, & manage**.
4. Select **Create** and copy the token.
5. In VS Code, create a file named `create_repos.py` outside any repository.
6. Paste this code and save:

   ```python
   import base64, getpass, json, urllib.error, urllib.request

   project = input("Project URL, such as https://dev.azure.com/<org>/<project>: ").strip().rstrip("/")
   apps = input("App IDs separated by ;: ")
   auth = base64.b64encode(f":{getpass.getpass('PAT: ')}".encode()).decode()
   for app in filter(None, (name.strip() for name in apps.split(";"))):
       request = urllib.request.Request(
           f"{project}/_apis/git/repositories?api-version=7.1", data=json.dumps({"name": app}).encode(),
           headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
       try:
           urllib.request.urlopen(request)
           print(f"Created {app}")
       except urllib.error.HTTPError as error:
           print(f"FAILED {app}: HTTP {error.code} {error.read().decode()}")
   ```

7. Open a terminal in VS Code (**Terminal → New Terminal**).
8. Run `python create_repos.py`. On macOS or Linux, run `python3 create_repos.py`.
9. Paste the project URL from your browser, the app IDs such as `my_app;other_app`, and the token.
10. Check that each app prints `Created`. `already exists` means the repository is there; Onboard stops if it
    has commits.
11. Delete `create_repos.py`. Revoke the token in **Personal access tokens**.

HTTP 401 means the token is wrong or expired. HTTP 403 means your account lacks **Create repository**; ask a
project administrator.

### One at a time

1. Open **Repos**.
2. Open the repository list at the top and select **New repository**.
3. Keep **Repository type** as **Git**.
4. Enter the app ID as **Repository name**. Match its case exactly.
5. Clear **Add a README**. Keep **Add a .gitignore** as **None**. The repository must be empty.
6. Select **Create**.

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
