# release.py commands

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
  app id and writes `<app-id>.patch` and `<app-id>-summary.md`. The summary
  lists deployed changes, target `local/` files, source `local/` files, and
  user files.
- `tag` (no arguments) uses no environment variables beyond the app id
  fallback above.

`bump` only changes versions on pull request runs with `refs/heads/...`
source and target branches. The `tag` command writes `APP_ID` and
`APP_VERSION` as Azure Pipelines variables for the feed publish step.

Azure Pipelines maps the variable group's `ACS_TOKEN` to `STACK_TOKEN`.
