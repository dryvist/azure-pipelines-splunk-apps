# Releases and versions

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

## Review the production diff

Before merging a pull request, open its validation run and download
**Artifacts** → `prod-diff-<attempt>`. It holds three files:

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
- `<app-id>-merged.tar.gz` contains the merged target app without `local/`,
  `metadata/local.meta`, or `users/`.

## Compare nonprod with prod

Run the `compare-nonprod-prod` pipeline with a list of app ids. It exports
each app from both stacks and writes the same summary and patch per app to
the `compare` artifact. Production is the target; nonprod is the source.
