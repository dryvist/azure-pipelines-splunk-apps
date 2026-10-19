# App pipeline setup

[Home](/Home) > [Getting started](/Getting-started) > App pipeline setup

[[_TOC_]]

Steps 7 through 10 create the pipeline, permit its resources, add the main
branch validation policy, and check the first pull request run.

## Step 7: Create a pipeline from the YAML file

**Where:** **Pipelines → New pipeline → Azure Repos Git**

**Do:**

1. Select the app repository, not `azure-pipelines-splunk-apps`.
2. Choose **Existing Azure Pipelines YAML file**.
3. Select `/azure-pipelines.yml`.
4. If using a custom name, enter a name that identifies the app.
5. Save the pipeline.

**Verify:**

1. Confirm the pipeline page shows the app repository.
2. Confirm the pipeline page shows its `azure-pipelines.yml` file.

## Step 8: Permit the pipeline to use its resources

**Where:** **Repos → Branches** and
**Pipelines → Pipelines → `<pipeline>`**

**Do:**

Run from a branch other than `main`: a `main` run also runs the `release` stage,
which publishes to the feed and pushes a tag.

1. Go to **Repos → Branches → repository selector**.
2. Select the app repository.
3. Go to **Repos → Branches → New branch**.
4. Select `main` as the branch to base the new branch on.
5. Enter a branch name other than `main`.
6. Create the branch.
7. Go to **Pipelines → Pipelines → `<pipeline>`**.
8. Select **Run pipeline**.
9. Select the new branch.
10. Select **Run**.

When Azure DevOps reports that a resource needs authorization:

1. Select **Permit** for `azure-pipelines-splunk-apps`.
2. Select **Permit** for `splunk-appinspect`.
3. Select **Permit** for `splunk-nonprod`.
4. Select **Permit** for `splunk-prod`.
5. Select **Permit** for `splunk-nonprod` as an environment.

If no Permit banner appears, authorize each variable group:

1. Open **Pipelines → Library → `splunk-appinspect` → Pipeline
   permissions**.
2. Select **+**.
3. Select the pipeline.
4. Open **Pipelines → Library → `splunk-nonprod` → Pipeline permissions**.
5. Select **+**.
6. Select the pipeline.
7. Open **Pipelines → Library → `splunk-prod` → Pipeline permissions**.
8. Select **+**.
9. Select the pipeline.

If no Permit banner appears, authorize each environment:

1. Open **Pipelines → Environments → `splunk-nonprod`**.
2. Select **⋮ → Security → Pipeline permissions**.
3. Select **+**.
4. Select the pipeline.

**Verify:**

1. Confirm the run proceeds past resource authorization.
2. Confirm the shared repository is authorized for the pipeline.
3. Confirm `splunk-appinspect` is authorized for the pipeline.
4. Confirm `splunk-nonprod` is authorized for the pipeline.
5. Confirm `splunk-prod` is authorized for the production comparison.
6. Confirm `splunk-nonprod` is authorized as an environment for the pipeline.

## Step 9: Add the `main` Build validation policy

**Where:** **Repos → Branches → main → Branch policies → Build
validation → +**

**Do:**

1. Select the app pipeline.
2. Set the policy to **Automatic**.
3. Set the policy to **Required**.
4. Save the policy.

Azure Repos uses this branch policy to queue pull request validation. The YAML
`trigger` queues runs for commits to `main`; Azure Repos ignores YAML `pr:`.

**Verify:**

1. Confirm the Build validation policy for `main` lists the app pipeline.
2. Confirm the policy requires the app pipeline to pass.

## Step 10: Check the first pull request run

**Where:** **Repos → Pull requests → New pull request**; then open the
pipeline run and **Artifacts**.

**Do:**

1. Select the app branch as the source branch.
2. Select `main` as the target branch.
3. Create the pull request.
4. Confirm `build` packages the app.
5. Confirm `build` publishes `dist`.
6. Confirm `appinspect` reads the `private_victoria` results.
7. Confirm `appinspect` reads the `future` results.
8. Confirm the failure count is 0.
9. Confirm the error count is 0.
10. Confirm the manual checks count is 0.
11. Confirm `appinspect` passes.
12. If `future_failure` is above 0, confirm the run shows a warning.
13. Confirm `nonprod` installs the package on the nonprod stack.
14. Confirm `proddiff` exports production.
15. Confirm `proddiff` creates a diff.
16. Open the `appinspect` job's **Show AppInspect JSON report** step.
17. Confirm that step prints the full JSON report.
18. Open the **Show AppInspect HTML report link** step.
19. Select the link.
20. Open `appinspect-report-<attempt>` with the highest attempt number.
21. Download `appinspect-report.html`.
22. Open `appinspect-report.html` in a browser.
23. Open `prod-diff-<attempt>` with the highest attempt number.
24. Confirm it contains `<app-id>-tree.txt` and `<app-id>.patch`.
25. Confirm it contains `<app-id>-summary.md`.

Each job attempt publishes its own artifact, so a rerun keeps earlier
reports and adds a new one with the next attempt number.

If the app is not installed in production yet, the export log shows
`NOT INSTALLED <app-id>`. The stage continues, and the summary lists every
package file as added.

**Verify:**

1. Confirm `build` succeeds.
2. Confirm `appinspect` succeeds.
3. Confirm `nonprod` succeeds.
4. Confirm `proddiff` succeeds.
5. Confirm the run has a `dist` artifact.
6. Confirm the run has an `appinspect-report-1` artifact.
7. Confirm the run has a `prod-diff-1` artifact.

## Related

- [App pipeline](/Pipelines/App-pipeline)

---

[< Previous: App repository](/Getting-started/App-repository) |
[Next: Release setup >](/Getting-started/Release)
