# Artifacts and diff reports

[Home](/Home) > [Reference](/Reference) > Artifacts and diff reports

[[_TOC_]]

The `dist` artifact carries the package between app stages. AppInspect and
compare artifacts include the job attempt. Each app pipeline compare job
publishes `<side>-diff-<app-id>-<attempt>`.

The `nonproddiff` artifacts are `nonprod-diff-<app-id>-<attempt>` and
`itsi-nonprod-diff-<app-id>-<attempt>`. The `proddiff` artifacts are
`prod-diff-<app-id>-<attempt>` and `itsi-prod-diff-<app-id>-<attempt>`.
Each artifact contains these reports:

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

The nonprod compare adds the summary to the run summary tab. The compare
artifacts contain the raw file tree, HTML report, summary, patch,
local-versus-default report, and merged archive for each app. The separate
compare pipeline can select two environments and export all custom apps when
the app list is `all` or empty.

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
- [Import from nonprod or prod](/Pipelines/App-import)

---

[< Previous: Variable groups](/Reference/Variable-groups) |
[Next: Reading logs >](/Reference/Reading-logs)
