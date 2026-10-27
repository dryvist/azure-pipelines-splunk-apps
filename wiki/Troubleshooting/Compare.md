# Compare troubleshooting

Use this page to fix compare exports that lack a search head value.

## Search head is empty or not configured

**Symptom:** The smoke-test job prints `FAIL <group>: empty value for
SPLUNK_SEARCH_HEAD`, or ACS reports that the search head is not configured or
not added.

**Fix:**

1. Add `SPLUNK_SEARCH_HEAD` to `splunk-itsi-nonprod` or `splunk-itsi-prod`.
2. Set it to the search head name for the same stack as `SPLUNK_STACK`.
3. Create the ACS token on that search head with audience `acs` using [Environments and ACS access](/Getting-started/Environments-and-ACS).
4. Set the variable lock state using [Reference: Variable groups](/Reference/Variable-groups).
5. Rerun the failed job.

For parameter names, see [Compare pipeline](/Pipelines/Compare-pipeline).
