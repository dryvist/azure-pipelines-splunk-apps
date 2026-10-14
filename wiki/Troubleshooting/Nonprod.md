# Nonprod troubleshooting

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Nonprod troubleshooting

[[_TOC_]]

## Nonprod stage

![Nonprod export, comparison artifact, and deployment path.](../diagrams/nonprod-stage.png)

### ACS token is rejected or lacks access

**Symptom:** An ACS command returns HTTP 401 or 403 during login, export, or
install.

**Cause:** `SPLUNK_STACK` may name the wrong target. The token may have the
wrong audience, may be from a different stack or search head, or lack an ACS
capability.

**Fix:**

1. Set `SPLUNK_STACK` to the stack name used in its service URL.
2. Create the token on that stack or its selected search head.
3. Set the token audience to `acs`.
4. Grant the account `export_apps`, `install_apps`, and `edit_local_apps`.
5. Put the token in `ACS_TOKEN` in the matching variable group.
6. Rerun the failed job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[ACS CLI](https://github.com/splunk/acs-cli).

### Agent address is missing from the ACS allowlist

**Symptom:** ACS requests from an agent fail even though stack and token
settings are correct.

**Cause:** The agent's outbound address is not allowed for one or both ACS
features used by the pipeline.

**Fix:**

1. Add the agents' outbound addresses to the `acs` feature allowlist.
2. Add the agents' outbound addresses to the `search-api` feature allowlist.
3. Rerun the failed job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## Related

- [Nonprod stage](/Stages/Nonprod)

---

[< Previous: AppInspect troubleshooting](/Troubleshooting/AppInspect) |
[Next: Proddiff troubleshooting >](/Troubleshooting/Proddiff)
