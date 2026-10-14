# release.py commands

[[_TOC_]]

The app id comes from `[id] name` in `package/default/app.conf`. If missing,
the script uses `BUILD_REPOSITORY_NAME`, then the working directory name.

## Code layout

| File | Contents |
| --- | --- |
| `release.py` | Command list and CLI dispatch. |
| `splunk_release/__init__.py` | Package marker. |
| `splunk_release/azure.py` | Pipeline plan, artifact link, and log helpers. |
| `splunk_release/version.py` | App id, version changes, and Git operations. |
| `splunk_release/package.py` | Configuration sorting, staging, and packaging. |
| `splunk_release/appinspect.py` | AppInspect requests, polling, and reports. |
| `splunk_release/acs.py` | ACS CLI install, sessions, deployment, and export. |
| `splunk_release/compare.py` | Archive comparison and deployment reports. |

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`,
  `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and `BUILD_SOURCEVERSIONMESSAGE`.
- `package` (no arguments) runs `slim package` and writes
  `dist/<app-id>-<version>.tar.gz`.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `deploy <dir>` runs `acs apps install private` with `SPLUNK_STACK`,
  `STACK_TOKEN`, `SPLUNK_USERNAME`, and `SPLUNK_PASSWORD`.
- `status` runs `acs status current-stack -f structured` and warns when the
  output reports `restartRequired: true`.
- `wait-version <dir>` reads the version from the single
  `<app-id>-<version>.tar.gz` package and checks `acs apps describe` every
  three seconds for up to 300 seconds.
- `restart` runs `acs restart current-stack` and polls restart-required status
  every 30 seconds for up to 30 minutes.
- `export <dir> [app-id ...]` runs `acs apps export` with `SPLUNK_STACK` and
  `STACK_TOKEN`. It saves `<dir>/<app-id>.tgz` with default, local, and users
  content. With no app ids, it exports this app. An app that is not installed
  prints `NOT INSTALLED <app-id>`.
- `export <dir> --custom` pages through `acs apps list` in groups of 100,
  removes names returned by `acs apps list --splunkbase=true`, then exports
  the remaining apps.
- `export <dir> <package-dir>` gets the app id from the package filename and
  exports it to `<dir>/<app-id>/`.
- `diff <target-dir> <source-dir> <out-dir>` compares the archives for each
  app id after promoting local configuration into default files. It writes
  `<app-id>.patch`, `<app-id>-diff.html`, `<app-id>-summary.md`,
  `<app-id>-local-vs-default.diff`, and `<app-id>-merged.tar.gz`. The HTML
  report includes an indented folder tree, side-by-side file tables, and the
  local-versus-default report. The patch compares deployed defaults as unified
  diffs. The summary lists the tree, deployed changes, local files, and user
  files, and is uploaded to the run summary.
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
