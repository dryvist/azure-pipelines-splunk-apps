# azure-pipelines-splunk-apps

One shared Azure DevOps pipeline that releases any number of Splunk app repos to Splunk Cloud Platform.
Merge to `main`, and the pipeline does the rest:

1. Bumps `version` in both `[launcher]` and `[id]` of `package/default/app.conf`.
2. Regenerates `package/app.manifest` with the
   [Splunk Packaging Toolkit](https://pypi.org/project/splunk-packaging-toolkit/) (`slim`).
3. Commits both files back to `main` as `Release <app> <version> ***NO_CI***`. `***NO_CI***` stops the commit
   from starting another run.
4. Packages `package/` as `<repo-name>/` into `<repo-name>-<version>.tar.gz`.
5. Installs the package on each Splunk Cloud stack through the
   [Admin Config Service (ACS)](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual).
   It deploys to `dev` first, then to `prod` after someone approves. ACS runs AppInspect on upload, and a
   failed check fails the stage. Victoria and Classic experience stacks both work.

The bump level is **patch**. Put `[minor]` or `[major]` in the PR title to change it.

## What's in this repo

| File | Purpose |
| --- | --- |
| `release.py` | All the logic: `bump`, `package`, `deploy`. It needs only the Python standard library and `slim`. |
| `templates/splunk-app.yml` | The pipeline. Every app repo extends it. |
| `example/azure-pipelines.yml` | The file each app repo carries. It's identical in every repo. |
| `test_release.py` | Self-check for the version bump and the Classic upload body |

## Installation

Do steps 1–6 once per Azure DevOps project. Do step 7 for each app repo.

### Before you start

You need:

- **An Azure DevOps project** with Project Administrator rights. You'll create a repo, variable groups and
  environments, and set repo permissions.
- **One or more Splunk Cloud Platform stacks.** These steps use two, `dev` and `prod`.
- **A splunk.com account.** ACS requires an AppInspect token, which the pipeline gets with this account.
- **An agent that can reach the internet.** Microsoft-hosted agents (`ubuntu-latest`, the default) work as-is.
  A self-hosted agent needs `git`, Python 3.13 in its tool cache, and outbound HTTPS to `pypi.org`,
  `api.splunk.com` and `admin.splunk.com`.

### 1. Create this repo in Azure DevOps

In your project, open **Repos → New repository**. Name it `azure-pipelines-splunk-apps` and uncheck
**Add a README**. Then push this repo to it:

```sh
git clone https://github.com/<you>/azure-pipelines-splunk-apps.git   # or download this repo
cd azure-pipelines-splunk-apps
git remote set-url origin https://dev.azure.com/<organization>/<project>/_git/azure-pipelines-splunk-apps
git push -u origin HEAD:main
```

If you name it something else, update `name:` in `example/azure-pipelines.yml` to match. The same applies if
you keep it in a different project from your app repos.

### 2. Choose the agent pool (optional)

The default is the Microsoft-hosted `ubuntu-latest` pool. To use a self-hosted pool, edit the `pool` default in
`templates/splunk-app.yml`:

```yaml
  - name: pool
    type: object
    default:
      name: <your-agent-pool>
      # demands: [agent.name -equals <your-agent>]   # optional: pin one agent
```

Commit and push.

### 3. Create an ACS token on each stack

Do this on **each** stack:

1. Sign in to Splunk Web as a user with the `sc_admin` role.
2. Open **Settings → Tokens**. If token authentication is off, select **Enable Token Authentication**.
3. Select **New Token**. Set **User** to an `sc_admin` user and **Audience** to `acs`. Pick an expiration you
   will track, then **Create**.
4. Copy the token. Splunk shows it only once.

The stack name is the first part of the stack URL. For `https://my-stack.splunkcloud.com`, it's `my-stack`.

To check a stack's experience, open **Support & Services → About** in Splunk Web. The
**Splunk Cloud Platform Experience** field shows Victoria or Classic. Note it for step 4.

### 4. Create the variable groups

Open **Pipelines → Library → + Variable group**. Create one shared group plus one group per stack. Use the
lock icon to mark each secret.

| Group name | Variable | Secret? | Value |
| --- | --- | --- | --- |
| `splunk-appinspect` | `SPLUNK_USERNAME` | no | splunk.com username |
| | `SPLUNK_PASSWORD` | **yes** | splunk.com password |
| `splunk-dev` | `SPLUNK_STACK` | no | dev stack name, e.g. `my-dev-stack` |
| | `ACS_TOKEN` | **yes** | dev ACS token (step 3) |
| | `SPLUNK_EXPERIENCE` | no | `classic` for a Classic stack; leave it out for Victoria |
| `splunk-prod` | `SPLUNK_STACK` | no | prod stack name, e.g. `my-prod-stack` |
| | `ACS_TOKEN` | **yes** | prod ACS token (step 3) |
| | `SPLUNK_EXPERIENCE` | no | `classic` for a Classic stack; leave it out for Victoria |

Use these names exactly, because the template finds each group by name.

### 5. Create the environments

Open **Pipelines → Environments → New environment**, choose **Resource: None**, and create:

- `splunk-dev`
- `splunk-prod`. Then open it and go to **⋮ → Approvals and checks → + → Approvals**. Add the people who
  approve production releases.

### 6. Let the pipeline push the release commit

The pipeline commits the version bump back to `main`, so the pipeline's identity needs write access.

1. Open **Project settings → Repositories → Security** for all repos, or a single app repo's **Security** tab.
2. Select **`<project> Build Service (<organization>)`**.
3. Set **Contribute** to **Allow** and **Bypass policies when pushing** to **Allow**. Bypass is required if
   `main` has branch policies, such as required PRs.

If the push still fails with `TF401027`, your project may run jobs under the collection identity. Check
**Project settings → Pipelines → Settings → Limit job authorization scope**. Then grant the same two
permissions to **`Project Collection Build Service (<organization>)`**.

### 7. Add each app repo

The repo must look like this:

```text
<repo-name>/                 # repo name == app id, e.g. my_custom_app
├── azure-pipelines.yml      # copied from example/, unchanged
└── package/                 # raw app contents: default/, bin/, metadata/, ...
    └── default/app.conf
```

`package/default/app.conf` needs these keys. `[id] name` must equal the repo name, and the two `version`
values must match:

```ini
[id]
name = my_custom_app
version = 1.0.0

[launcher]
version = 1.0.0

[package]
id = my_custom_app
```

Then:

1. Copy the pipeline file into the app repo and merge it to `main`:

   ```sh
   cp azure-pipelines-splunk-apps/example/azure-pipelines.yml <app-repo>/azure-pipelines.yml
   ```

2. Open **Pipelines → New pipeline → Azure Repos Git →** the app repo **→ Existing Azure Pipelines YAML file →**
   `/azure-pipelines.yml`, then select **Run**.
3. The first run pauses with **"This pipeline needs permission to access resources."** Select **View → Permit**
   for each one: the `azure-pipelines-splunk-apps` repo, the variable groups and the environments. Do this
   once per app repo.
4. Watch it finish: **build** → **dev** → **prod**, where prod waits for approval. On a Victoria stack, check
   that the version on the stack matches:

   ```sh
   curl -s -H "Authorization: Bearer $ACS_TOKEN" \
     "https://admin.splunk.com/$SPLUNK_STACK/adminconfig/v2/apps/victoria/my_custom_app"
   ```

## Usage

Day to day:

1. Change files under `package/` on a branch and open a PR.
2. To bump more than the patch number, add `[minor]` or `[major]` to the PR title.
3. Merge. The pipeline bumps, commits, packages, deploys to dev, and waits for prod approval.

The build stage leaves out dotfiles, `__pycache__`, `*.pyc`/`*.pyo` and `tests/`. Don't edit versions or
`app.manifest` by hand, because the pipeline owns them.

To build a package locally, from an app repo root:

```sh
pip install splunk-packaging-toolkit
python <path-to>/azure-pipelines-splunk-apps/release.py package   # writes dist/<app>-<version>.tar.gz
python <path-to>/azure-pipelines-splunk-apps/test_release.py      # self-check
```

`release.py bump` commits and pushes, so run it only in CI.

### Customizing

| Change | How |
| --- | --- |
| Add a stack, e.g. `qa` | Add it to `environments` in the template, in deploy order. Create its `splunk-qa` variable group and environment. |
| Default branch isn't `main` | Change `include: [main]` in each app repo's `azure-pipelines.yml`. The push goes to whichever branch triggered the run. |
| Python version | `versionSpec` in the template. `slim` supports Python up to 3.13. |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `[launcher] and [id] need the same version` | Set both `version` values in `app.conf` to the same `x.y.z`. |
| slim: `must equal the name of the app folder` | Set `[id] name` in `app.conf` to the repo name. |
| `git push` fails (`TF401027` / `TF402455`) | Step 6 permissions are missing on that repo. |
| `HTTP 401` from `api.splunk.com` | The `splunk-appinspect` username or password is wrong. |
| `HTTP 401`/`403` from `admin.splunk.com` | The ACS token expired, has the wrong audience, or belongs to a user without `sc_admin`. |
| `HTTP 404` from `admin.splunk.com` | The `SPLUNK_STACK` name is wrong, or `SPLUNK_EXPERIENCE` doesn't match the stack. |
| `HTTP 4xx` listing AppInspect failures | Fix what the response lists. The run log prints the whole response. |
| Run waits on "needs permission" | Step 7.3: permit the resources. |
