# Smoke-test troubleshooting

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Smoke-test troubleshooting

[[_TOC_]]

## Smoke-test pipeline

![Smoke test login and export jobs feeding the result job.](../diagrams/smoke-test-pipeline.png)

### ACS reports `WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED`

**Symptom:** ACS returns HTTP 400 with
`WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED` while exporting the
built-in `search` app.

**Cause:** The built-in search app allows local and user configuration files
only. The smoke-test export is limited to those files. The compare pipeline
exports full app content, so do not include the built-in `search` app there.

**Fix:**

1. Keep the smoke-test export at `--default=false`.
2. Keep `--local=true` and `--users=true` for the smoke-test export.
3. Keep `--confs-only=true` for the smoke-test export.
4. Remove `search` from the compare pipeline app id list.
5. Rerun the affected job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[ACS CLI](https://github.com/splunk/acs-cli).

### Read the smoke-test result

**Symptom:** The `result` job prints `RESULT: FAILED`.

**Cause:** At least one of `appinspect`, `nonprod`, or `prod` did not finish
with `Succeeded`.

**Fix:**

1. Open each failed job named in the `Result` step output.
2. Read its first `FAIL` or `Error` line.
3. Fix that job's credential, network, or export issue.
4. Rerun the smoke-test pipeline.

**Docs:** [Conditions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions),
[logging commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands).

## Related

- [Smoke-test pipeline](/Pipelines/Smoke-test-pipeline)

---

[< Previous: Compare troubleshooting](/Troubleshooting/Compare) |
[Next: Reading the run log >](/Troubleshooting/Reading-logs)
