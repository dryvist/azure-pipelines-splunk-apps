# release.py commands

[Home](/Home) > [Reference](/Reference) > release.py commands

[[_TOC_]]

Every ACS command retries every 30 seconds for up to 15 minutes while ACS
returns `424-failed-dependency` or `503-service-unavailable`. Each retry prints
`ACS is busy with another deployment task, retrying in 30 seconds`.

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`,
  `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and `BUILD_SOURCEVERSIONMESSAGE`.
- `package` (no arguments) runs `slim package` and writes
  `dist/<app-id>-<version>.tar.gz`.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `deploy <dir>` runs `acs apps install private` with `SPLUNK_STACK` and
  `STACK_TOKEN`.
- `uninstall <dir>` runs `acs apps uninstall <app-id>` when `acs apps list`
  shows the app, and otherwise prints that it is not installed.
- `status` runs `acs status current-stack -f structured` and warns when the
  output reports `restartRequired: true`.
- `wait-version <dir>` reads the version from the single
  `<app-id>-<version>.tar.gz` package and checks `acs apps describe` every 15
  seconds for up to 15 minutes.
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
  changed paths. Files that differ only in line endings, trailing spaces or
  trailing blank lines count as unchanged in every compare. Each path shows its line count. A changed path also shows the
  share of lines added or removed, such as `8% (120 -> 135 lines)`.
- `local-diff <target-dir> <source-dir> <out-dir>` compares each target local
  file with the same stanzas in the source default file and writes
  `<app-id>-local-vs-default.diff`. Lines with `-` are target local settings;
  lines with `+` are source package defaults. It runs as its own step.
- `tree`, `local-diff` and `diff` accept `--reverse` as a last argument. It
  shows the source side as `-` and the target side as `+`. The nonprod import
  uses it, so its diffs show nonprod as `+`.
- `diff <target-dir> <source-dir> <out-dir>` merges local into default on both
  sides with ksconf, combining repeated stanzas as Splunk does, then compares the archives for each app id. It
  writes `<app-id>.patch`, `<app-id>-stanzas.txt`, `<app-id>-diff.html`,
  `<app-id>-summary.md`, and
  `<app-id>-merged.tar.gz`. The HTML report includes an indented folder tree
  and side-by-side file tables. The patch compares deployed defaults as unified
  diffs. The summary lists deployed changes, local files, and user files, and
  is uploaded to the run summary.
- `local-diff` and `diff` print each file's diff in a collapsed log group
  under a separator line. Select the file name to expand it. In `diff`, a
  changed file's name also shows the percent of lines changed.
  Before the line diffs, `diff` prints a `Changed stanzas` section: one
  collapsed group per `.conf` or `.meta` file, listing each added, removed or
  changed stanza and how many of its settings differ.
- `tree`, `local-diff`, `diff` and `import-nonprod` sort the rows of every
  CSV file on both sides, keeping the first row as the header. A CSV with a
  line break inside a quoted field stays as it is. The nonprod import writes
  the sorted CSV files to the pull request.
- `tree`, `local-diff`, `diff` and `import-nonprod` print the install
  checksums Splunk Cloud writes on its own, then leave them out of every
  compare and import: the `[app/install/install_source_checksum]` stanza in
  `metadata/local.meta`, and the `install_source_checksum` and
  `install_source_local_checksum` keys in every `app.conf`. AppInspect rejects
  both keys. A compare with no other change prints `NO DIFFERENCES`.
- `install-acs` downloads ACS CLI 2.26.0 for Linux or Windows x64 agents,
  verifies its SHA-256 checksum, extracts it to `AGENT_TEMPDIRECTORY`, prepends
  that directory to `PATH`, runs `acs version`, adds the selected stack, and
  logs in.
- `appinspect-link` prints the current build's AppInspect artifact link.
- `tag` (no arguments) uses no environment variables beyond the app id
  fallback above.
- `feed-check <app-id>` prints that the app is in the `splunk-apps` feed, or
  fails with `<app-id> is not in the splunk-apps feed; run its app pipeline on
  main to release it`. It reads `SYSTEM_ACCESSTOKEN`.
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
