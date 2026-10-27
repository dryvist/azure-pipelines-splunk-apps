# Smoke-test troubleshooting

Use this page to fix smoke-test credential, export, and result failures.

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
3. Fix that job's credential, network, or export issue.
4. Rerun the smoke-test pipeline.

For pipeline inputs, see [Smoke-test pipeline](/Pipelines/Smoke-test-pipeline).
