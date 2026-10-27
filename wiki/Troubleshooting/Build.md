# Build troubleshooting

Use this page to fix skipped stages, version bumps, package sorting, and artifact errors.

## A stage after AppInspect is skipped

1. Open the build job and read **Show stage plan**.
2. Check the trigger and stage conditions in [App](/Pipelines/App).
3. For pull request validation, confirm that the Build validation policy exists on `main`. See
   [Onboard: After onboarding](/Pipelines/Onboard#after-onboarding), step 5.
4. For a skipped `release` stage, run the pipeline from `main`.

## The version bump step prints a skip reason

**Symptom:** The step prints `target app.conf is missing, skipping bump`, or
`<branch> already changes the version, skipping bump`.

A run that pushes a bump prints `<app> bumped to <version>`. The bump commit starts a second run. That run
prints the skip and runs every stage. This pair of runs is expected.

1. If `package/default/app.conf` is missing, add it. See
   [Appendix: Create the repository and its files](/Setup/Appendix-manual-app#create-the-repository-and-its-files).
2. If the source and target versions differ, set the intended version in the source branch.
3. Confirm the pipeline log shows the expected version before rerunning.

## The version bump push is rejected

1. Follow the Build Service rights in [Build Service: App repository](/Setup/Build-service#app-repository).
2. Rerun pull request validation.

## `app.conf` has a version mismatch

1. Set the same `version` in `[launcher]` and `[id]` in `package/default/app.conf`.
2. Rerun the build.

## `ksconf sort` moves comments

Add `KSCONF-NO-SORT` to the file comment, then rerun the build.

## An artifact already exists

1. For fixed-name artifacts, start a new pipeline run.
2. For attempt-named reports or diffs, open the artifact with the job attempt number. See
   [Artifacts](/Reference/Artifacts).

If these steps do not fix the run, see [Reading logs](/Troubleshooting/Reading-logs).
