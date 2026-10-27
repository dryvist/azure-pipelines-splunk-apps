# App pipeline setup

New app? Use [Onboard an app](Onboard-app.md). The steps below are the manual fallback.

Create the app pipeline, permit its resources, require pull request validation, and check the first run.

## Step 7: Create the app pipeline

**Where:** **Pipelines → New pipeline → Azure Repos Git**

1. Select the app repository. Do not select `azure-pipelines-splunk-apps`.
2. Select **Existing Azure Pipelines YAML file**.
3. Select `/azure-pipelines.yml`.
4. If you use a custom name, enter a name that identifies the app.
5. Select **Save**.

**Verify:** The pipeline page shows the app repository and `azure-pipelines.yml`.

## Step 8: Permit the pipeline to use its resources

Run from a branch other than `main`. A `main` run also runs the `release` stage, which publishes to the feed and pushes a tag.

1. Select **Repos → Branches**.
2. Select the app repository.
3. Select **New branch**.
4. Select `main` as the base branch.
5. Enter a branch name other than `main`.
6. Create the branch.
7. Select **Pipelines**.
8. Select the app pipeline.
9. Select **Run pipeline**.
10. Select the new branch.
11. Select **Run**.
12. Permit each requested resource. See [Permissions troubleshooting](/Troubleshooting/Permissions).
13. Rerun the pipeline if authorization stopped the run.

The first run usually requests `azure-pipelines-splunk-apps`, `splunk-appinspect`, `splunk-nonprod`, `splunk-prod`, and the `splunk-nonprod` environment.

## Step 9: Require pull request validation

1. Select **Repos → Branches**.
2. Select `main`.
3. Open **Branch policies**.
4. Add a **Build validation** policy.
5. Select the app pipeline.
6. Set the policy to **Automatic**.
7. Set the policy to **Required**.
8. Save the policy.

**Verify:** The `main` policy lists the app pipeline and requires it to pass. For how pull request runs start, see [App pipeline](/Pipelines/App-pipeline).

## Step 10: Check the first pull request run

1. Select **Repos → Pull requests**.
2. Select **New pull request**.
3. Select the app branch as the source branch.
4. Select `main` as the target branch.
5. Create the pull request.
6. Open the pipeline run. Check each row in the table below.
7. In the `appinspect` job, open the **Show AppInspect HTML report link** step and select the link.
8. Open the `appinspect-report-<attempt>` artifact with the highest attempt number. Download `appinspect-report.html` and open it in a browser.

| Stage or job | Expected result |
| --- | --- |
| `build` | Succeeds and publishes `dist`. |
| `appinspect` | Succeeds. Failure, error, and manual check counts are 0. |
| `nonproddiff` | Shows **Compare with nonprod**. Both jobs finish without installing. |
| `nonprod` | Shows **Deploy to nonprod** and installs the package. |
| `proddiff` | Shows **Compare with prod**. Both jobs finish without installing. |

The **Show AppInspect JSON report** step prints the full report. A `future_failure` count above 0 shows a warning.

If the app is not in prod yet, the export log shows `NOT INSTALLED <app-id>`. Every package file shows as added.

The `prod-diff-<app-id>-<attempt>` and `itsi-prod-diff-<app-id>-<attempt>` artifacts hold the reports listed in [Artifacts](/Reference/Artifacts).

**Verify:** The run has `dist`, `appinspect-report-1`, and `prod-diff-<app-id>-1` artifacts.

If a step fails, use [Troubleshooting](/Troubleshooting).
