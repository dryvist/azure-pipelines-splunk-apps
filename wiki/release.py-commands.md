# release.py commands

[[_TOC_]]

The app id comes from `[id] name` in `package/default/app.conf`. If missing,
the script uses `BUILD_REPOSITORY_NAME`, then the working directory name.

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`,
  `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and `BUILD_SOURCEVERSIONMESSAGE`.
- `package` (no arguments) runs `slim package` and writes
  `dist/<app-id>-<version>.tar.gz`.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `deploy <dir>` runs `acs apps install private` with `SPLUNK_STACK`,
  `STACK_TOKEN`, `SPLUNK_USERNAME`, and `SPLUNK_PASSWORD`.
- `export <dir> [app-id ...]` runs `acs apps export` with `SPLUNK_STACK` and
  `STACK_TOKEN`. It saves `<dir>/<app-id>.tgz` with default, local, and users
  content. With no app ids, it exports this app. An app that is not installed
  prints `NOT INSTALLED <app-id>`.
- `diff <target-dir> <source-dir> <out-dir>` compares the archives for each
  app id after promoting local configuration into default files. It writes
  `<app-id>.patch`, `<app-id>-summary.md`, and
  `<app-id>-merged.tar.gz`. The patch compares only `default/` and
  `metadata/default.meta` as unified diffs with `target/` and `source/` paths.
  The merged archive contains the target app without `local/`,
  `metadata/local.meta`, or `users/`. The summary lists those deployed changes,
  local files, and user files.
- `install-acs` downloads ACS CLI 2.26.0 for Linux or Windows x64 agents,
  verifies its SHA-256 checksum, extracts it to `AGENT_TEMPDIRECTORY`, and
  prepends that directory to the Azure Pipelines path.
- `appinspect-link` prints the current build's AppInspect artifact link.
- `tag` (no arguments) uses no environment variables beyond the app id
  fallback above.

`bump` only changes versions on pull request runs with `refs/heads/...`
source and target branches. The `tag` command writes `APP_ID` and
`APP_VERSION` as Azure Pipelines variables for the feed publish step.

Azure Pipelines maps the variable group's `ACS_TOKEN` to `STACK_TOKEN`.
