# Permissions and first run

Use this page when a run asks for permission, or cannot find a repository, variable group, or deployment environment.

## Variable group is not found or not authorized

**Symptom:** The run reports `Variable group <name> was not found`, or it says **This pipeline needs permission**.

**Cause:** Group names must match the pipeline reference exactly. These pipelines use hyphens, such as `splunk-appinspect`, not underscores.

**Fix:**

1. Compare each requested group name with the names in **Pipelines → Library**.
2. Rename any group that uses underscores to the exact hyphenated name. The mapping is in [Variable groups](/Reference/Variable-groups).
3. Select **View** in the permission banner.
4. Select **Permit** for each requested repository, variable group, and deployment environment.
5. Rerun the pipeline if authorization stopped the run.

If no banner appears, authorize the pipeline on each group and environment:

1. Open **Pipelines → Library** and open the group.
2. Open **Pipeline permissions**.
3. Select **+**.
4. Select the pipeline.
5. For an environment, open **Pipelines → Environments** and open the environment.
6. Select **⋮**.
7. Select **Security**.
8. Select **Pipeline permissions**.
9. Select **+**.
10. Select the pipeline.

## `A template expression is not allowed in this context` for `pool`

**Symptom:** Pipeline validation rejects the `pool` template expression.

**Fix:**

1. Open the pipeline and select **Edit**.
2. Select **⋮**, then select **Triggers**.
3. Select the **YAML** tab.
4. Select the configured pool in **Default agent pool for YAML**. See [Manual pipeline setup](/Getting-started/Manual-pipeline).
5. In an app repository, set `pool` under the template's `parameters`. See [App repository](/Getting-started/App-repository).

## Import pull request receives HTTP 403

**Symptom:** `Open a pull request with the <env> app` fails with HTTP 403.

**Fix:** Follow Step 6 in [App repository](/Getting-started/App-repository). It allows the Build Service
**Contribute to pull requests** permission. Then rerun the import pipeline.
