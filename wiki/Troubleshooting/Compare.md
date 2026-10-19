# Compare troubleshooting

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Compare troubleshooting

[[_TOC_]]

## Compare pipeline

The compare pipeline selects source and target environments at run time. An
app list of `all`, or an empty one, exports every custom app. The compare job
uses target as the first diff input and source as the second.

![Environment exports feeding a comparison artifact.](../diagrams/compare-any-environments.png)

### Search head is empty or not configured

**Symptom:** The smoke-test job prints `FAIL <group>: empty value for
SPLUNK_SEARCH_HEAD`, or ACS reports that the search head is not configured or
not added.

**Cause:** The selected ITSI variable group lacks the exact
`SPLUNK_SEARCH_HEAD` name or value. Azure then passes the literal
`$(SPLUNK_SEARCH_HEAD)`. The script sets the target with
`acs config add-stack --target-sh`.

**Fix:**

1. Set the exact variable name `SPLUNK_SEARCH_HEAD` in the selected ITSI group.
2. Set it to the search head name for the same stack as `SPLUNK_STACK`.
3. Create the ACS token on that search head with audience `acs`.
4. Keep `SPLUNK_SEARCH_HEAD` unlocked in the variable group.
5. Rerun the failed job.

**Docs:** [ACS CLI](https://github.com/splunk/acs-cli),
[ACS export apps][acs-export],
[variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups).

## Related

- [Compare pipeline](/Pipelines/Compare-pipeline)
- [Variable groups](/Reference/Variable-groups)

---

[< Previous: Deploy troubleshooting](/Troubleshooting/Deploy) |
[Next: Smoke-test troubleshooting >](/Troubleshooting/Smoke-test)

[acs-export]: https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform
