# Permissions and first run

Use this page when a run asks for permission, or cannot find a repository, variable group, or deployment
environment.

## First run

Each pipeline requests the variable groups and environments listed for it in
[Reference: Variable groups](/Reference/Variable-groups). The App pipeline usually requests
`azure-pipelines-splunk-apps`, `splunk-appinspect`, `splunk-nonprod`, `splunk-prod`, and the `splunk-nonprod`
environment.

## Variable group is not found or not authorized

**Symptom:** The run reports `Variable group <name> was not found`, or it says **This pipeline needs permission**.

**Cause:** Group names must match the pipeline reference exactly. These pipelines use hyphens, such as
`splunk-appinspect`, not underscores.

**Fix:**

1. Compare each requested group name with the names in **Pipelines → Library**.
2. Rename any group that uses underscores to the exact hyphenated name. See
   [Variable groups](/Reference/Variable-groups).
3. Select **View** in the permission banner.
4. Select **Permit** for each requested repository, variable group, and deployment environment.
5. Rerun the pipeline if authorization stopped the run.

If no banner appears, authorize the pipeline on each group and environment:

1. Open **Pipelines → Library** and open the group. Open **Pipeline permissions**. Select **+**, then select
   the pipeline.
2. For an environment, open **Pipelines → Environments** and open the environment. Select **⋮**, then
   **Security**, then **Pipeline permissions**. Select **+**, then select the pipeline.

## `A template expression is not allowed in this context` for `pool`

**Symptom:** Pipeline validation rejects the `pool` template expression.

**Fix:**

1. Open the pipeline and select **Edit**.
2. Select **⋮**, then **Triggers**. Select the **YAML** tab.
3. Select the configured pool in **Default agent pool for YAML**. See
   [Manual pipelines](/Setup/Manual-pipelines).
4. In an app repository, set `pool` under the template's `parameters`. See
   [Onboard: After onboarding](/Pipelines/Onboard#after-onboarding).

## Import pull request receives HTTP 403

**Symptom:** `Open a pull request with the <env> app` fails with HTTP 403.

**Fix:** Allow the app repository's Build Service **Contribute to pull requests** right. See
[Build Service: App repository](/Setup/Build-service#app-repository). Then rerun the import pipeline.
