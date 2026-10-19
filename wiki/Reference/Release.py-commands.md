# release.py commands

[Home](/Home) > [Reference](/Reference) > release.py commands

[[_TOC_]]

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`,
  `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and `BUILD_SOURCEVERSIONMESSAGE`.
- `package` (no arguments) runs `slim package` and writes
  `dist/<app-id>-<version>.tar.gz`.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `deploy <dir>` runs `acs apps install private` with `SPLUNK_STACK` and
  `STACK_TOKEN`.
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
- `tree <target-dir> <source-dir> <out-dir>` compares all raw files in each
  app before merging and writes `<app-id>-tree.txt` with added, removed, and
  changed paths.
- `local-diff <target-dir> <source-dir> <out-dir>` compares each target local
  file with the same stanzas in the source default file and writes
  `<app-id>-local-vs-default.diff`. It runs as its own step.
- `diff <target-dir> <source-dir> <out-dir>` merges local into default on both
  sides with `ksconf merge`, then compares the archives for each app id. It
  writes `<app-id>.patch`, `<app-id>-diff.html`, `<app-id>-summary.md`, and
  `<app-id>-merged.tar.gz`. The HTML report includes an indented folder tree
  and side-by-side file tables. The patch compares deployed defaults as unified
  diffs. The summary lists deployed changes, local files, and user files, and
  is uploaded to the run summary.
- `install-acs` downloads ACS CLI 2.26.0 for Linux or Windows x64 agents,
  verifies its SHA-256 checksum, extracts it to `AGENT_TEMPDIRECTORY`, prepends
  that directory to `PATH`, runs `acs version`, adds the selected stack, and
  logs in.
- `appinspect-link` prints the current build's AppInspect artifact link.
- `tag` (no arguments) uses no environment variables beyond the app id
  fallback above.
- `import-nonprod <export-dir>` merges local app configuration into default,
  removes `local/`, `users/`, and `metadata/local.meta`, sets both version rows
  to one patch above `main`, regenerates `app.manifest`, commits the package,
  pushes a new import branch, and opens a pull request to `main`. It uses
  `BUILD_BUILDID`, `BUILD_REPOSITORY_ID`, `BUILD_REPOSITORY_NAME`,
  `SYSTEM_ACCESSTOKEN`, `SYSTEM_COLLECTIONURI`, `SYSTEM_TEAMPROJECT`, and
  `SYSTEM_TEAMPROJECTID`.

ACS setup maps the variable-group `ACS_TOKEN` to `STACK_TOKEN`. It runs
once per job; later steps reuse the CLI configuration.
`SPLUNK_SEARCH_HEAD` selects a target search head when configured.

`bump` only changes versions on pull request runs with `refs/heads/...`
source and target branches. The `tag` command writes `APP_ID` and
`APP_VERSION` as Azure Pipelines variables for the feed publish step.

## Related

- [Code layout](/Reference/Code-layout)
- [Artifacts](/Reference/Artifacts)
- [Import from nonprod](/Pipelines/Nonprod-import)

---

[Next: Code layout >](/Reference/Code-layout)
