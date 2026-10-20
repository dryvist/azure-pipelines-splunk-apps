# Proddiff troubleshooting

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Proddiff troubleshooting

[[_TOC_]]

## Proddiff stage

![Production comparison stage.](../diagrams/proddiff-stage.png)

### Diff output is missing or unexpected

**Symptom:** A production compare artifact is missing, or the file tree or
summary shows added, changed, or removed files.

**Cause:** The export or diff command failed, or production differs from the
package. The tree step compares raw files. Local files are compared with
matching package defaults in a separate step. The merged-default step merges
local into default with ksconf, combines repeated stanzas, sorts defaults, and
compares deployed files.

**Fix:**

1. Open the `proddiff` stage, displayed as **Compare with prod**.
2. Read the first failed export or diff step in either compare job.
3. Open `prod-diff-<app-id>-<attempt>` or
   `itsi-prod-diff-<app-id>-<attempt>` for that job attempt.
4. Review the file tree, local-versus-default report, patch, and summary.
5. Update the app package or resolve the production difference before merge.

**Docs:** [release.py commands](/Reference/Release.py-commands),
[ksconf filter](https://ksconf.readthedocs.io/en/stable/cmd_filter.html),
[ksconf diff](https://ksconf.readthedocs.io/en/stable/cmd_diff.html),
[ksconf sort](https://ksconf.readthedocs.io/en/stable/cmd_sort.html).

## Related

- [Proddiff stage](/Stages/Proddiff)
- [Artifacts](/Reference/Artifacts)

---

[< Previous: Nonprod troubleshooting](/Troubleshooting/Nonprod) |
[Next: Release troubleshooting >](/Troubleshooting/Release)
