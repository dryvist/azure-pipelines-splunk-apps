# Smoke-test troubleshooting

Use this page to fix smoke-test credential, ACS, REST, Azure DevOps, export,
and result failures.

## Smoke-test pipeline

![Smoke test login and export jobs feeding the result job.](../diagrams/smoke-test-pipeline.png)

Create and run the pipeline by following [Smoke-test pipeline](/Pipelines/Smoke-test-pipeline).

### Credentials or ACS export fails

**Symptom:** A check prints `FAIL <group>: empty value for <names>`, returns
HTTP 401 or 403, or fails before or after listing apps.

**Fix:**

1. Fill in each named variable in the reported group.
2. For AppInspect login failures, check the account username and password.
3. For ACS login failures, check `SPLUNK_STACK`, `ACS_TOKEN`, and
   `SPLUNK_SEARCH_HEAD` when using `splunk-itsi`.
4. If app listing succeeds but export fails, grant `export_apps` to the ACS
   token account.
5. Rerun the failed job.

**Verify:** Confirm the job prints its `PASS` lines for login, app listing,
and export.

### ACS status or app listing fails

**Symptom:** A `nonprod` or `prod` job fails at the stack status, app listing,
or `search` app version check. The error names `acs status current-stack`,
`acs apps list`, or `acs apps describe search`.

**Fix:**

1. Check that `SPLUNK_STACK` and `ACS_TOKEN` in the job's group belong to the
   same stack.
2. Check the ACS token's role in Splunk Cloud ACS. The role must allow reading
   the stack status and the apps.
3. Rerun the failed job.

**Verify:** Confirm the job prints `PASS` lines for the stack status, the app
listings, and the `search` app version.

### Search head REST read fails

**Symptom:** The search head REST check returns HTTP 401 or 403. Or it prints
`SPLUNK_SEARCH_HEAD is set, so set SPLUNK_REST_URL`.

**Fix:**

1. For `splunk-itsi`, set `SPLUNK_REST_URL` in the `splunk-itsi-<environment>`
   group to `https://<search-head>:8089`.
2. Check that the agent can reach that URL on port 8089.
3. Check that the ACS token is accepted by that search head.
4. Rerun the failed job.

**Verify:** Confirm the job prints `PASS ... search head REST: token accepted`.
The line also says whether the `launcher` stanza was found. `not found` still
means the token was accepted.

### Azure DevOps rights fail

**Symptom:** The `azuredevops` job prints `FAIL azure-devops:` for a variable
group, an environment, or a Build Service right. It can also return HTTP 401,
403, or 404.

**Fix:**

1. For a missing variable group, create it. See
   [Variable groups](/Getting-started/Variable-groups). For a missing
   environment, create it. See
   [Environments and ACS access](/Getting-started/Environments-and-ACS).
2. Authorize the pipeline on the group or environment. See
   [Variable group is not found or not authorized](/Troubleshooting/Permissions#variable-group-is-not-found-or-not-authorized).
3. For Create repository, open **Project settings → Repositories → Security**.
   Select `<project> Build Service (<org>)`. Set **Create repository** to
   **Allow**.
4. For Contribute to pull requests, open the **Security** page of this
   repository. Set **Contribute to pull requests** to **Allow** for
   `<project> Build Service (<org>)`. Use
   [App repository step 6](/Getting-started/App-repository#step-6-grant-build-service-permissions-on-the-app-repository)
   for this repository.
5. For the splunk-apps feed, follow steps 4 to 6 in
   [Package feed](/Getting-started/Feed).
6. Rerun the `azuredevops` job.

### ACS reports `WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED`

**Symptom:** ACS returns HTTP 400 with
`WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED` while exporting the
built-in `search` app.

**Fix:**

1. Keep the smoke-test export at `--default=false`.
2. Keep `--local=true` and `--users=true` for the smoke-test export.
3. Keep `--confs-only=true` for the smoke-test export.
4. Remove `search` from the compare pipeline app id list.
5. Rerun the affected job.

**Docs:** [ACS export apps][acs-export], [ACS CLI][acs-cli].

[acs-export]: https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform
[acs-cli]: https://github.com/splunk/acs-cli

### Read the smoke-test result

**Symptom:** The `result` job prints `RESULT: FAILED`.

**Fix:**

1. Open each failed job named in the `Result` step output.
2. Read its first `FAIL` or `Error` line.
3. Fix that job's credential, network, ACS, REST, or rights issue.
4. Rerun the smoke-test pipeline.

For pipeline inputs, see [Smoke-test pipeline](/Pipelines/Smoke-test-pipeline).
