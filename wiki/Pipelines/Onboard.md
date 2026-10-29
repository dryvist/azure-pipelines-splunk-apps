# Onboard pipeline

The Onboard pipeline fills a new repository's empty `package/` from an app installed on a stack. It then creates the app
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

A script creates one repository per app, named exactly the app ID. Each repository gets `azure-pipelines.yml`
with the `AGENT_POOL` agent pool from `splunk-appinspect` and an empty `package/` folder. The script also adds the Onboard and Deploy pipelines to each
repository's **Pipeline permissions**. Run it, then [run Onboard](#run-it).

First, grant the Build Service rights once for all repositories. See
[Build Service: App repository](/Setup/Build-service#app-repository).

1. In Azure DevOps, open **User settings** (top right), then **Personal access tokens**.
2. Select **New Token**. Set **Expiration** to 1 day.
3. Under **Scopes**, select **Custom defined**. Select **Code: Read, write, & manage**,
   **Build: Read & execute**, and **Variable Groups: Read**.
4. Select **Create** and copy the token.
5. In VS Code, open a folder outside any repository.
6. Optional: create a file named `.env` in that folder with one line, `AZURE_DEVOPS_EXT_PAT=<token>`. The script
   then does not ask for the token.
7. Create a file named `create_repos.py` in that folder.
8. Paste this code and save:

   ```python
   import base64, getpass, json, pathlib, urllib.error, urllib.request

   env = pathlib.Path(".env")
   pat = next((line.split("=", 1)[1].strip().strip("\"'") for line in env.read_text().splitlines()
               if line.startswith("AZURE_DEVOPS_EXT_PAT=")), "") if env.exists() else ""
   project = input("Project URL, such as https://dev.azure.com/<org>/<project>: ").strip().rstrip("/")
   apps = input("App IDs separated by ;: ")
   pat = pat or getpass.getpass("PAT: ")
   headers = {"Authorization": "Basic " + base64.b64encode(f":{pat}".encode()).decode(),
              "Content-Type": "application/json"}

   def call(path, body=None, method=None):
       request = urllib.request.Request(f"{project}/_apis/{path}", headers=headers, method=method,
                                        data=json.dumps(body).encode() if body else None)
       return json.load(urllib.request.urlopen(request))

   groups = call("distributedtask/variablegroups?groupName=splunk-appinspect&api-version=7.1")["value"]
   pool = next((g["variables"].get("AGENT_POOL", {}).get("value", "") for g in groups), "") or input(
       "Agent pool for the app pipelines (blank uses Microsoft-hosted agents): ").strip()
   yaml = call("git/repositories/azure-pipelines-splunk-apps/items?path=/example/azure-pipelines.yml"
               "&includeContent=true&$format=json&api-version=7.1")["content"]
   yaml = yaml.replace("<agent-pool>", pool) if pool else yaml.split("    # Remove pool")[0]
   # Onboard and Deploy check out app repositories.
   uses = ("onboard/azure-pipelines.yml", "deploy/azure-pipelines.yml")
   pipelines = [d["id"] for d in call("build/definitions?includeAllProperties=true&api-version=7.1")["value"]
                if d.get("process", {}).get("yamlFilename", "").endswith(uses)]
   for app in filter(None, (name.strip() for name in apps.split(";"))):
       try:
           repo = call("git/repositories?api-version=7.1", {"name": app})
           call(f"git/repositories/{repo['id']}/pushes?api-version=7.1", {
               "refUpdates": [{"name": "refs/heads/main", "oldObjectId": "0" * 40}],
               "commits": [{"comment": "feat: add the app pipeline", "changes": [
                   {"changeType": "add", "item": {"path": path},
                    "newContent": {"content": text, "contentType": "rawtext"}}
                   for path, text in (("/azure-pipelines.yml", yaml), ("/package/.gitkeep", ""))]}]})
           print(f"Created {app}")
       except urllib.error.HTTPError as error:
           print(f"FAILED {app}: HTTP {error.code} {error.read().decode()}")
           continue
       try:
           if len(pipelines) < len(uses):
               raise LookupError("create the Onboard and Deploy pipelines first")
           call(f"pipelines/pipelinePermissions/repository/{repo['project']['id']}.{repo['id']}"
                "?api-version=7.1-preview.1",
                {"pipelines": [{"id": i, "authorized": True} for i in pipelines]}, "PATCH")
           print(f"Onboard and Deploy can use {app}")
       except (LookupError, urllib.error.HTTPError) as error:
           print(f"Select Permit for {app} when Onboard or Deploy runs: {error}")
   ```

9. Open a terminal in VS Code (**Terminal → New Terminal**).
10. Run `python create_repos.py`. On macOS or Linux, run `python3 create_repos.py`.
11. Paste the project URL from your browser.
12. Enter the app IDs, such as `my_app;other_app`.
13. If `splunk-appinspect` has no `AGENT_POOL`, enter the agent pool name. Leave it blank to use
    Microsoft-hosted agents.
14. Enter the token if the script asks for it.
15. Check that each app prints `Created` and `Onboard and Deploy can use`.
16. Delete `create_repos.py` and `.env`. Revoke the token in **Personal access tokens**.

HTTP 401 means the token is wrong or expired. HTTP 403 means your account lacks **Create repository**; ask a
project administrator. HTTP 409 means the repository already exists. `Select Permit` means the script could not
add the pipelines; select **Permit** for that repository when Onboard or Deploy runs.

## Run it

1. Open the Onboard pipeline and select **Run pipeline**.
2. Select `nonprod` or `prod` for **environment**.
3. Keep `splunk-itsi` for **target**, or select `splunk` for the main search head.
4. Enter the app IDs for **App IDs**, such as `my_app;other_app`.
5. Select **Run**.
6. Select **Permit** for any resource the run asks for. See [Permissions](/Troubleshooting/Permissions).

Each job exports its app, writes the export to `package/`, pushes the commit to `main`, and creates the app
pipeline. It works on an empty repository too. If the repository has no `azure-pipelines.yml`, the job adds the
example file with the `AGENT_POOL` pool from `splunk-appinspect`. Without `AGENT_POOL`, it uses Microsoft-hosted
agents.

## After onboarding

Do these steps once for each new app repository.

1. Run the app pipeline on `main`. That run goes through every stage described in [App](/Pipelines/App).
2. Add the Build validation policy on `main`. Onboard does not add it. Open **Repos → Branches**, select
   `main`, and open **Branch policies**. Add a **Build validation** policy, select the app pipeline, set the
   policy to **Automatic** and **Required**, and save.
