# Proddiff troubleshooting

Use this page to fix missing or unexpected production comparison reports.

## Proddiff stage

![Production comparison stage.](../diagrams/proddiff-stage.png)

### Diff output is missing or unexpected

**Symptom:** A production compare artifact is missing, or the file tree or
summary shows added, changed, or removed files.

**Fix:**

1. Open the `proddiff` stage, displayed as **Compare with prod**.
2. Read the first failed export or diff step in either compare job.
3. Open `prod-diff-<app-id>-<attempt>` or
   `itsi-prod-diff-<app-id>-<attempt>` for that job attempt.
4. Review the file tree, local-versus-default report, patch, and summary.
5. Update the app package or resolve the production difference before merge.

For compare job order, see [Proddiff stage](/Stages/Proddiff). For report contents, see [Artifacts](/Reference/Artifacts).
