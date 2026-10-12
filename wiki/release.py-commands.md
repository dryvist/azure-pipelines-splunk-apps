# release.py commands

The app id comes from `[id] name` in `package/default/app.conf`. If missing,
the script uses `BUILD_REPOSITORY_NAME`, then the working directory name.

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`,
  `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and `BUILD_SOURCEVERSIONMESSAGE`.
- `package` (no arguments) uses no environment variables beyond the app id
  fallback above.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `deploy <dir>` uses `SPLUNK_STACK`, `ACS_TOKEN`, `SPLUNK_USERNAME`, and
  `SPLUNK_PASSWORD`.
- `export <dir>` uses `SPLUNK_STACK` and `ACS_TOKEN`.
- `diff <pkg-dir> <dir>` uses no environment variables beyond the app id
  fallback above.
- `tag` (no arguments) uses no environment variables beyond the app id
  fallback above.

`bump` only changes versions on pull request runs with `refs/heads/...`
source and target branches. The `tag` command writes `APP_ID` and
`APP_VERSION` as Azure Pipelines variables for the feed publish step.
