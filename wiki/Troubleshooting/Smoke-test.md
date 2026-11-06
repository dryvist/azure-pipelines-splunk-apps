# Smoke-test troubleshooting

Use this page to fix [smoke test](/Pipelines/Smoke-test) failures.

## Credentials or ACS export fails

**Symptom:** A check prints `FAIL <group>: empty value for <names>`, returns HTTP 401 or 403, or fails before or
after listing apps.

**Fix:**

1. Fill in each named variable in the reported group.
2. For AppInspect login failures, check the account username and password.
3. For ACS login failures, check `SPLUNK_STACK`, `ACS_TOKEN`, and `SPLUNK_SEARCH_HEAD` when using `splunk-itsi`.
4. If app listing succeeds but export fails, grant `export_apps` to the ACS token account.
5. Rerun the failed job.

**Verify:** The job prints its `PASS` lines for login, app listing, and export.

## ACS status or app listing fails

**Symptom:** A `nonprod` or `prod` job fails at the stack status, app listing, or `search` app version check. The
error names `acs status current-stack`, `acs apps list`, or `acs apps describe search`.

**Fix:**

1. Check that `SPLUNK_STACK` and `ACS_TOKEN` in the job's group belong to the same stack.
2. Check the ACS token's role in Splunk Cloud ACS. The role must allow reading the stack status and the apps.
3. Rerun the failed job.

**Verify:** The job prints `PASS` lines for the stack status, the app listings, and the `search` app version.

## Search head REST read fails

**Symptom:** The **Test port 8089** step shows a `WARN ... port 8089` warning with HTTP 401 or 403, or no HTTP
status. The warning shows the agent public IP, the host, the addresses the host resolves to, and whether port 443
on that host is open. The `result` job repeats it. Repair and saved searches need port 8089.

| Warning shows | Cause |
| --- | --- |
| HTTP 401 | The token is not valid on that search head. |
| HTTP 403, or no status with port 443 open | Port 8089 alone is blocked: the `search-api` IP allow list or a firewall. |
| No status with port 443 failed | The host is not reachable from the agent network at all. |
| `not resolved` | `SPLUNK_STACK` or `SPLUNK_SEARCH_HEAD` is wrong. |

**Fix:**

1. Check that `SPLUNK_SEARCH_HEAD` and `SPLUNK_STACK` in the job's group are correct. They set the REST URL. See
   [Reference: Variable groups](/Reference/Variable-groups).
2. Check that the agent public IP is in the `search-api` IP allow list. Splunk Cloud blocks port 8089 from any other
   address.
3. Check that a firewall between the agents and Splunk Cloud allows port 8089 to the host's addresses. Allow it by
   host name, because the addresses can change.
4. Check that the ACS token is accepted by that search head.
5. Rerun the failed job.

**Verify:** The step prints `PASS ... port 8089 search head REST: token accepted`. The line also says whether the `launcher`
stanza was found. `not found` still means the token was accepted.

## Azure DevOps rights fail

**Symptom:** The `azuredevops` job prints `FAIL azure-devops:` for a variable group, an environment, or a Build
Service right. It can also return HTTP 401, 403, or 404.

**Fix:**

1. For a missing variable group, create it. See [Variable groups](/Setup/Variable-groups). For a missing
   environment, create it. See [Environments and ACS](/Setup/Environments-and-ACS).
2. Authorize the pipeline on the group or environment. See
   [Permissions](/Troubleshooting/Permissions#variable-group-is-not-found-or-not-authorized).
3. For Contribute to pull requests, see [Build Service: App repository](/Setup/Build-service#app-repository).
4. For the splunk-apps feed, see [Package feed](/Setup/Feed).
5. Rerun the `azuredevops` job.

## Read the smoke-test result

**Symptom:** The `result` job prints `RESULT: FAILED`.

**Fix:**

1. Open each failed job named in the `Result` step output. See
   [Smoke test: Read the result](/Pipelines/Smoke-test#read-the-result).
2. Read its first `FAIL` or `Error` line.
3. Fix that job's credential, network, ACS, REST, or rights issue.
4. Rerun the smoke-test pipeline.
