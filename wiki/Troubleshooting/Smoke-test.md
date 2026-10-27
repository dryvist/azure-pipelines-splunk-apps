# Smoke-test troubleshooting

Use this page to fix smoke-test credential, ACS, REST, Azure DevOps, export, and result failures.

To create and run the pipeline, follow [Smoke test](/Pipelines/Smoke-test).

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

**Symptom:** The **Test port 8089** step returns HTTP 401 or 403, or cannot connect.

**Fix:**

1. Check that `SPLUNK_SEARCH_HEAD` and `SPLUNK_STACK` in the job's group are correct. They set the REST URL. See
   [Reference: Variable groups](/Reference/Variable-groups).
2. Check that the agents' public IP addresses are in the `search-api` IP allow list. Splunk Cloud blocks port
   8089 from any other address.
3. Check that the ACS token is accepted by that search head.
4. Rerun the failed job.

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
3. For Create repository, see [Build Service: Project rights](/Setup/Build-service#project-rights-for-onboard).
4. For Contribute to pull requests, see [Build Service: App repository](/Setup/Build-service#app-repository).
5. For the splunk-apps feed, see [Package feed](/Setup/Feed).
6. Rerun the `azuredevops` job.

## ACS reports `WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED`

**Symptom:** ACS returns HTTP 400 with `WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED` while exporting the
built-in `search` app.

The smoke-test export uses `--default=false`, `--local=true`, `--users=true`, and `--confs-only=true`.

**Fix:**

1. Remove `search` from the compare pipeline app ID list.
2. Rerun the affected job.

**Docs:** [ACS export apps][acs-export], [ACS CLI][acs-cli].

## Read the smoke-test result

**Symptom:** The `result` job prints `RESULT: FAILED`.

**Fix:**

1. Open each failed job named in the `Result` step output.
2. Read its first `FAIL` or `Error` line.
3. Fix that job's credential, network, ACS, REST, or rights issue.
4. Rerun the smoke-test pipeline.

For how to read the result, see [Smoke test: Read the result](/Pipelines/Smoke-test#read-the-result).

[acs-export]: https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform
[acs-cli]: https://github.com/splunk/acs-cli
