# Artifacts and diff reports

[Home](/Home) > [Reference](/Reference) > Artifacts and diff reports

[[_TOC_]]

The `dist` artifact carries the package between app stages. AppInspect and
diff artifacts include the job attempt. Compare export and compare artifacts
use fixed names.

A Proddiff `prod-diff-<attempt>` contains these reports:

- `<app-id>-tree.txt`: raw target and source file tree with added, removed,
  and changed paths.
- `<app-id>-diff.html`: folder tree and side-by-side changed-file tables.
- `<app-id>-summary.md`: deployed changes, target local files, source local
  files,
  and user files. Target local files remain after deployment, override defaults,
  and are not backed up.
- `<app-id>.patch`: changes under `default/` and `metadata/default.meta`.
- `<app-id>-local-vs-default.diff`: production local files against package
  defaults.
- `<app-id>-merged.tar.gz`: merged app without `local/`,
  `metadata/local.meta`, or `users/`.

The nonprod artifact is named `nonprod-diff-<app-id>-<attempt>`. The same
summary is added to the run summary tab. The compare artifact contains the raw
file tree, HTML report, summary, patch, local-versus-default report, and merged
archive for each app. Compare can select two environments and export all
custom apps when the app list is `all` or empty.

The app import run publishes `nonprod-diff-<app-id>-<attempt>` before it
creates a pull request. Review this artifact alongside the proposed changes.

## Compare release tags

Open **Repos → Files → Compare** and select the two Git tags.

## Download a release package

Open **Artifacts → splunk-apps**, then select the app id and version.

![Package and installed target comparison.](../diagrams/diff-build.png)

## Related

- [Proddiff stage](/Stages/Proddiff)
- [Compare pipeline](/Pipelines/Compare-pipeline)
- [Import from nonprod](/Pipelines/Nonprod-import)

---

[< Previous: Variable groups](/Reference/Variable-groups) |
[Next: Reading logs >](/Reference/Reading-logs)
