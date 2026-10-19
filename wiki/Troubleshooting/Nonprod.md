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

**Docs:** [ACS CLI](https://github.com/splunk/acs-cli),
[ACS export apps][acs-export].

### Agent address is missing from the ACS allowlist

**Symptom:** ACS requests from an agent fail even though stack and token
settings are correct.

**Cause:** The agent's outbound address is not allowed for one or both ACS
features used by the pipeline.

**Fix:**

1. Add the agents' outbound addresses to the `acs` feature allowlist.
2. Add the agents' outbound addresses to the `search-api` feature allowlist.
3. Rerun the failed job.

**Docs:** [agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[ACS export apps][acs-export].

### App is not installed in nonprod

**Symptom:** The export logs `NOT INSTALLED <app-id>`, then the import step
reports that the `.tgz` export is missing.

**Cause:** The compare steps can continue without an installed target app,
but the import command needs the exported app archive.

**Fix:**

1. Install the app in nonprod through the app deployment pipeline.
2. Confirm the export step writes `<app-id>.tgz` under
   `nonprod-export/<app-id>/`.
3. Run the import option again.

**Docs:** [Nonprod stage](/Stages/Nonprod),
[Import from nonprod](/Pipelines/Nonprod-import).

## Related

- [Nonprod stage](/Stages/Nonprod)

---

[< Previous: AppInspect troubleshooting](/Troubleshooting/AppInspect) |
[Next: Proddiff troubleshooting >](/Troubleshooting/Proddiff)

[acs-export]: https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform
