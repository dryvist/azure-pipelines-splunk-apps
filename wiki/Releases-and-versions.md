# Releases and versions

[[_TOC_]]

## Version bumps

On pull request runs, `release.py bump` compares the app version with the
target branch. It bumps the version only when both version rows match and the
target branch has not changed the version.

- `[major]` in the commit message increments major and resets minor and patch.
- `[minor]` increments minor and resets patch to zero.
- Otherwise, the patch number increments.

The bump updates the `version` values in `[launcher]` and `[id]`, regenerates
`app.manifest`, commits both files, and pushes the commit to the pull request
source branch.

## Tags and feed packages

After AppInspect passes on `main`, the release stage pushes the Git tag
`v<version>` for the current commit. It publishes the built package as a
Universal Package to the `splunk-apps` feed. Its name is the lowercase app id
and its version is the app version.

To compare two releases:

1. Open **Repos → Files → Compare**.
2. Select the two Git tags.

To download a release:

1. Open **Artifacts → splunk-apps**.
2. Select the app id and version.

To install a feed package, run the manual deploy pipeline and select the
environment and app ids. Production approvals apply through `splunk-prod`.

## Review the production diff

Before merging a pull request, open its validation run and download
**Artifacts** → `prod-diff-<attempt>`. It holds five files:

- `<app-id>-diff.html` shows a folder tree and side-by-side tables for each
  changed deployed file. It also includes the local-versus-default report.
- `<app-id>-summary.md` lists the changes in sections:
  - **Deployed changes:** files under `default/` and
    `metadata/default.meta` that the deploy adds, changes, or removes.
  - **Target local files:** files in production `local/` and
    `metadata/local.meta`. They stay after a deploy, override the deployed
    defaults, and are not backed up.
  - **Source local files:** files in the package `local/`, if present.
  - **User files:** files under `users/` on each side.
- `<app-id>.patch` shows line changes only under `default/` and
  `metadata/default.meta`.
- `<app-id>-local-vs-default.diff` compares production local files with the
  matching stanzas in the package defaults.
- `<app-id>-merged.tar.gz` contains the merged target app without `local/`,
  `metadata/local.meta`, or `users/`.
- The same summary is added to the run summary tab.

## Compare environments

Run the `compare-environments` pipeline and select source and target as
`nonprod` or `prod`. Leave the app list empty to export all custom apps, or
enter app ids. The `compare` artifact contains the HTML report, summary,
patch, local-versus-default report, and merged archive for each app.
