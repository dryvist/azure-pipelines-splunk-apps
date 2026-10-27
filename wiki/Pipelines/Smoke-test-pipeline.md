# Smoke-test pipeline

Use this page to create and run the pipeline that checks AppInspect login,
read-only Splunk Cloud ACS and search head access for nonprod and prod, and
the Azure DevOps rights that the app pipelines use.

The `target` value is `splunk` or `splunk-itsi`. The `result` job runs after
the four check jobs, including when a check fails.

Complete setup steps 1 to 4 in [Getting started](/Getting-started) before you
run this pipeline.

The checks do not install, uninstall, restart, or write to a stack or to Azure
DevOps. See [release.py commands](/Reference/Release.py-commands) for the ACS
setup lifecycle.

## Create the pipeline

| Pipeline name | YAML path |
| --- | --- |
| `smoke-test` | `/smoke-test/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

## Run the pipeline

1. Select **Run pipeline**.
2. Select `splunk` or `splunk-itsi` for `target`.
3. Select **Run**.
4. Permit requested resources using [Permissions troubleshooting](/Troubleshooting/Permissions).

**Verify:** Confirm the `appinspect`, `nonprod`, `prod`, `azuredevops`, and
`result` jobs finish.

## Read the result

1. Open the run.
2. Open the `result` job.
3. Select the **Result** step.
4. Read its last line:

```text
RESULT: ALL PASS
RESULT: FAILED - open each failed job for its FAIL or Error line
```

## Checks

Each check prints one `PASS` line. A failed check prints one `FAIL <group>:`
line.

| Check | What it proves | Fix |
| --- | --- | --- |
| `appinspect`: AppInspect login | The `splunk-appinspect` account logs in to splunk.com. Bulk Splunkbase commands use it too. | [Credentials][cred] |
| `nonprod`, `prod`: ACS login and app list | `SPLUNK_STACK` and `ACS_TOKEN` reach ACS and list apps. | [Credentials][cred] |
| `nonprod`, `prod`: export | The token exports the built-in `search` app's local and user files. | [Credentials][cred] |
| `nonprod`, `prod`: stack status | ACS returns the stack status and whether a restart is required. | [ACS][acs] |
| `nonprod`, `prod`: app listings | ACS lists installed apps and Splunkbase apps. Compare reads these lists for its custom export. | [ACS][acs] |
| `nonprod`, `prod`: search app version | ACS describes the `search` app. The deploy wait reads the same value. | [ACS][acs] |
| `nonprod`, `prod`: search head REST | The stack token reads the `launcher` stanza of the `search` app over REST. Repair reads the same API. | [REST][rest] |
| `azuredevops`: onboard resources | Each variable group and environment that onboard authorizes can be found. | [Azure DevOps][ado] |
| `azuredevops`: splunk-apps feed | The job token reads the `splunk-apps` feed. | [Azure DevOps][ado] |
| `azuredevops`: Create repository | The Build Service has Create repository on the project. | [Azure DevOps][ado] |
| `azuredevops`: Contribute to pull requests | The Build Service has Contribute to pull requests on this repository. | [Azure DevOps][ado] |
| `result`: job results | Each job result, and whether all of them succeeded. | [Result][result] |

Not checked: bulk installs and updates, restarts, uninstalls, pull request
creation, feed publishing, and ACS app permissions. The Azure DevOps checks read
only this repository, not the app repositories.

See [Variable groups](/Reference/Variable-groups) for the groups that `target`
selects.

If a check fails, use [Smoke-test troubleshooting](/Troubleshooting/Smoke-test).

[cred]: /Troubleshooting/Smoke-test#credentials-or-acs-export-fails
[acs]: /Troubleshooting/Smoke-test#acs-status-or-app-listing-fails
[rest]: /Troubleshooting/Smoke-test#search-head-rest-read-fails
[ado]: /Troubleshooting/Smoke-test#azure-devops-rights-fail
[result]: /Troubleshooting/Smoke-test#read-the-smoke-test-result
