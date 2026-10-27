# Compare troubleshooting

Use this page to fix compare exports that lack a search head value. Use it also when a production compare
output is missing or unexpected.

## Search head is empty or not configured

**Symptom:** The smoke-test job prints `FAIL <group>: empty value for SPLUNK_SEARCH_HEAD`. Or ACS reports that
the search head is not configured or not added.

**Fix:**

1. Add `SPLUNK_SEARCH_HEAD` to `splunk-itsi-nonprod` or `splunk-itsi-prod`.
2. Set it to the search head name for the same stack as `SPLUNK_STACK`.
3. Create the ACS token on that search head with audience `acs`. See
   [Environments and ACS](/Setup/Environments-and-ACS).
4. Set the variable lock state as listed in [Reference: Variable groups](/Reference/Variable-groups).
5. Rerun the failed job.

For parameter names, see [Compare pipeline](/Pipelines/Compare).

## Diff output is missing or unexpected

**Symptom:** A production compare artifact is missing. Or the file tree or summary shows added, changed, or
removed files.

**Fix:**

1. Open the `proddiff` stage, displayed as **Compare with prod**.
2. Read the first failed export or diff step in either compare job.
3. Open `prod-diff-<app-id>-<attempt>` or `itsi-prod-diff-<app-id>-<attempt>` for that job attempt.
4. Review the file tree, the local-versus-default report, the patch, and the summary.
5. Update the app package, or resolve the production difference, before the merge.

![Production comparison stage.](../diagrams/proddiff-stage.png)

For compare job order, see [Reference: Stages](/Reference/Stages#proddiff). For report contents, see
[Artifacts](/Reference/Artifacts).
