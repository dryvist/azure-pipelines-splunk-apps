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

To compare two releases, open **Repos → Files → Compare** and select the two
Git tags. To download a release, open **Artifacts → splunk-apps**, then select
the app id and version.

## Review the production diff

Before merging a pull request, open its validation run and download
`prod-diff.patch` from **Artifacts → prod-diff**. Review the file changes
against the proposed package. The `proddiff` stage exports production content
when available. Without an export archive, the patch shows package files as
additions.
