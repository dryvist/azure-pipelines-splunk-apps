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
- `uninstall <dir>` prints a DANGER warning: the uninstall permanently deletes
  ALL of the app's lookups (CSV files) and local settings. It runs `acs apps
  uninstall <app-id> --scope local`, which removes the copy installed on the
  target search head only, such as one installed in Splunk Web. It then runs
  `acs apps uninstall <app-id>`, which removes the copy on all search heads. A
  404 from either means there is no such copy. It then waits as described below
  until `acs apps describe` no longer finds the app.
- `status` runs `acs status current-stack -f structured` and warns when the
  output reports `restartRequired: true`.
- `wait-version <dir>` reads the version from the single
  `<app-id>-<version>.tar.gz` package and waits until `acs apps describe`
  reports exactly that version in its `version` field. Each check that does
  not match prints the version ACS reports, or `not installed`.
- `uninstall` and `wait-version` check every 15 seconds for up to 15 minutes.
  They finish only when `acs status current-stack` reports
  `infrastructure.status` `Ready` and the app change shows in `acs apps
  describe`. A `Failed` stack status fails the step. A 401 Unauthorized from
  ACS, which happens while a search head restarts, counts as not ready yet.
- `restart` runs `acs restart current-stack` when `acs status current-stack`
  reports `restartRequired: true`, then waits as `uninstall` and
  `wait-version` do, for up to 30 minutes, until restart-required status
  clears. `restart --force` always restarts and prints a warning to check the
  uninstall steps.
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
  Changes under `users/` and `lookups/lookup_file_backups/` print in one
  collapsed group per folder, and `diff` prints its summary's user files in a
  collapsed `User files` group.
- `local-diff <target-dir> <source-dir> <out-dir>` compares each target local
  file with the same stanzas in the source default file and writes
  `<app-id>-local-vs-default.diff`. Lines with `-` are target local settings;
  lines with `+` are source package defaults. It runs as its own step.
- `data-models <target-dir> <source-dir> <out-dir>` merges local into default
  on both sides, then compares each `default/data/models/*.json` file. It
  formats the JSON with one key per line and sorted keys, skips files that
  differ only in formatting, prints each model in its own collapsed group, and
  writes `<app-id>-data-models.patch`. `diff` leaves data models out of its
  patch, stanza list, and HTML report; its summary still lists them.
- `tree`, `local-diff` and `diff` accept `--reverse` as a last argument. It
  shows the source side as `-` and the target side as `+`. The import
  uses it, so its diffs show the exported environment as `+`.
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
- `tree`, `local-diff`, `diff` and `import` sort the rows of every
  CSV file on both sides, keeping the first row as the header. A CSV with a
  line break inside a quoted field stays as it is. A CSV that cannot be read
  stays as it is and prints one warning. The import writes
  the sorted CSV files to the pull request.
- `tree`, `local-diff`, `diff` and `import` print the install
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
- `import <env> <export-dir> [--skip-lookups] [--skip-lookup-backups]`
  merges local app configuration into default, removes `local/`, `users/`,
  and `metadata/local.meta`, sets both version rows
  to one patch above the highest of `main` and the splunk-apps feed versions,
  regenerates `app.manifest`, commits the package,
  pushes a new `<env>-import/` branch, and opens a pull request to `main`. It uses
  `BUILD_BUILDID`, `BUILD_REPOSITORY_ID`, `BUILD_REPOSITORY_NAME`,
  `SYSTEM_ACCESSTOKEN`, `SYSTEM_COLLECTIONURI`, `SYSTEM_TEAMPROJECT`, and
  `SYSTEM_TEAMPROJECTID`. `--skip-lookups` keeps the `lookups/` folder on
  `main`. `--skip-lookup-backups` leaves out `lookups/lookup_file_backups/`.
  The compare commands take the same two options and remove those folders on
  both sides.
- `repair-packages <dir> <out-dir> <conf> <stanzas>` checks that each stanza
  is on the search head and in the package's `default/<conf>.conf`. It writes
  `<out-dir>/temp` one patch above the highest feed or installed version
  without those stanzas, and `<out-dir>/real` one patch above that with the
  package content unchanged. It sets `REPAIR_VERSION`.
  Stanza names are separated by `;`. It reads `SYSTEM_ACCESSTOKEN`.
- `delete-local <dir> <conf> <stanzas>` deletes each stanza's local copy
  through the search head REST API. A stanza with no local copy prints
  `has no local copy`.
- `repair-check <dir> <conf> <stanzas>` exports the app and fails when a
  stanza still has a local copy or is missing.

ACS setup maps the variable-group `ACS_TOKEN` to `STACK_TOKEN`. It runs
once per job; later steps reuse the CLI configuration.
`SPLUNK_SEARCH_HEAD` selects a target search head when configured. The REST
API commands use `SPLUNK_REST_URL`, or
`https://<SPLUNK_STACK>.splunkcloud.com:8089` when no search head is set.

`bump` only changes versions on pull request runs with `refs/heads/...`
source and target branches. It bumps from the highest of the target version
and the splunk-apps feed versions, and reads `SYSTEM_ACCESSTOKEN`. The `tag` command writes `APP_ID` and
`APP_VERSION` as Azure Pipelines variables for the feed publish step.

## Related

- [Code layout](/Reference/Code-layout)
- [Artifacts](/Reference/Artifacts)
- [Import from nonprod or prod](/Pipelines/App-import)

---

[Next: Code layout >](/Reference/Code-layout)
