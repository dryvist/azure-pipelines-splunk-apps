# release.py commands

Use this page to look up what each `release.py` command does. Run the commands from the repository root. Pipelines
call them from job steps.

Every ACS command retries every 30 seconds for up to 15 minutes while ACS returns `424-failed-dependency` or
`503-service-unavailable`. Each retry prints `ACS is busy with another deployment task, retrying in 30 seconds`.

## Build and package

- `bump` (no arguments) uses `SYSTEM_PULLREQUEST_TARGETBRANCH`, `SYSTEM_PULLREQUEST_SOURCEBRANCH`, and
  `BUILD_SOURCEVERSIONMESSAGE`. It changes versions only on pull request runs with `refs/heads/...` source and
  target branches. It bumps from the highest of the target version and the splunk-apps feed versions. It reads
  `SYSTEM_ACCESSTOKEN`.
- `package` (no arguments) runs `slim package` and writes `dist/<app-id>-<version>.tar.gz`.
- `tag` (no arguments) uses no environment variables beyond the app ID fallback above. It writes `APP_ID` and
  `APP_VERSION` as Azure Pipelines variables for the feed publish step.
- `feed-check <app-id>` prints that the app is in the `splunk-apps` feed. Otherwise it fails with
  `<app-id> is not in the splunk-apps feed; run its app pipeline on main to release it`. It reads
  `SYSTEM_ACCESSTOKEN`.
- `appinspect <dir>` uses `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.
- `appinspect-link` prints the current build's AppInspect artifact link.
- `plan` prints each stage the run executes, with the rule behind each one. It reads `BUILD_REASON` and
  `BUILD_SOURCEBRANCH`. The **Show stage plan** step runs it.

## Deploy, wait, and restart

- `deploy <dir>` runs `acs apps bulk-install private --package-src-dir <dir>` once, for every
  `<app-id>-<version>.tar.gz` package in the directory, with `SPLUNK_STACK` and `STACK_TOKEN`.
- `uninstall <dir>` prints a DANGER warning for each app. The uninstall permanently deletes ALL of the app's
  lookups (CSV files) and local settings. It writes the app IDs of every package in the directory to a JSON
  file. Then it runs `acs apps bulk-uninstall --file <file>` once, which removes the apps from all search heads.
  It then waits until every app is gone.
- `status` runs `acs status current-stack -f structured`. It warns when the output reports `restartRequired: true`.
- `wait-version <dir>` reads the version from each `<app-id>-<version>.tar.gz` package in the directory. It waits
  until `acs apps describe` reports exactly that version in its `version` field for every app. Each check that
  does not match prints the version ACS reports, or `not installed`.
- `uninstall` and `wait-version` check every 15 seconds for up to 15 minutes. They finish only when
  `acs status current-stack` reports `infrastructure.status` `Ready`, and every app change is confirmed. A
  `Failed` stack status fails the step. A 401 Unauthorized from ACS, which happens while a search head restarts,
  counts as not ready yet.
- `restart` runs `acs restart current-stack` only when `acs status current-stack` reports `restartRequired: true`.
  It then waits for up to 30 minutes, until the restart-required status clears.
- `acs <args...>` runs an ACS CLI command with the job's ACS configuration. The bulk pipelines use it.

## Export and compare

- `export <dir> [app-id ...]` runs `acs apps export` with `SPLUNK_STACK` and `STACK_TOKEN`. It saves
  `<dir>/<app-id>.tgz` with default, local, and users content. With no app IDs, it exports this app. An app that
  is not installed prints `NOT INSTALLED <app-id>`.
- `export <dir> --custom` pages through `acs apps list` in groups of 100. It removes names returned by
  `acs apps list --splunkbase=true`, then exports the remaining apps.
- `export <dir> <package-dir>` gets the app ID from the package filename. It exports the app to `<dir>/<app-id>/`.
- `tree <target-dir> <source-dir> <out-dir>` compares all raw files in each app before merging. It writes
  `<app-id>-tree.txt` with added, removed, and changed paths. Each path shows its line count. A changed path also
  shows the share of lines added or removed, such as `8% (120 -> 135 lines)`. Files that differ only in line
  endings, trailing spaces, or trailing blank lines count as unchanged. Changes under `users/` and
  `lookups/lookup_file_backups/` print in one collapsed group per folder. The `diff` summary's user files print in
  a collapsed `User files` group.
- `local-diff <target-dir> <source-dir> <out-dir>` compares each target local file with the same stanzas in the
  source default file. It writes `<app-id>-local-vs-default.diff`. Lines with `-` are target local settings.
  Lines with `+` are source package defaults. It runs as its own step.
- `data-models <target-dir> <source-dir> <out-dir>` merges local into default on both sides. Then it compares
  each `default/data/models/*.json` file. It formats the JSON with one key per line and sorted keys. It skips
  files that differ only in formatting. It prints each model in its own collapsed group, and writes
  `<app-id>-data-models.patch`. `diff` leaves data models out of its patch, stanza list, and HTML report. Its
  summary still lists them.
- `diff <target-dir> <source-dir> <out-dir>` merges local into default on both sides with ksconf, combining
  repeated stanzas as Splunk does. It compares the archives for each app ID. It writes `<app-id>.patch`,
  `<app-id>-stanzas.txt`, `<app-id>-diff.html`, `<app-id>-summary.md`, and `<app-id>-merged.tar.gz`. The HTML
  report includes an indented folder tree and side-by-side file tables. The patch compares deployed defaults as
  unified diffs. The summary lists deployed changes, local files, and user files, and it is uploaded to the run
  summary.
- `local-diff` and `diff` print each file's diff in a collapsed log group under a separator line. Select the file
  name to expand it. In `diff`, a changed file's name also shows the percent of lines changed. Before the line
  diffs, `diff` prints a `Changed stanzas` section. It has one collapsed group per `.conf` or `.meta` file, which
  lists each added, removed, or changed stanza and how many of its settings differ.
- `tree`, `local-diff`, and `diff` accept `--reverse` as a last argument. The source side then shows as `-`, and
  the target side as `+`. The import uses it, so its diffs show the exported environment as `+`.
- `tree`, `local-diff`, `diff`, and `import` sort the rows of every CSV file on both sides, and keep the first row
  as the header. A CSV with a line break inside a quoted field stays as it is. A CSV that cannot be read stays as
  it is, and prints one warning. The import writes the sorted CSV files to the pull request.
- `tree`, `local-diff`, `diff`, and `import` print the install checksums that Splunk Cloud writes. Then they leave
  them out of every compare and import. The checksums are the `[app/install/install_source_checksum]` stanza in
  `metadata/local.meta`, and the `install_source_checksum` and `install_source_local_checksum` keys in every
  `app.conf`. A compare with no other change prints `NO DIFFERENCES`.

## Onboard and import

- `import <env> <export-dir> [--skip-lookups] [--skip-lookup-backups]` merges local app configuration into
  default. It removes `local/`, `users/`, and `metadata/local.meta`. It sets both version rows to one patch above
  the highest of `main` and the splunk-apps feed versions. It regenerates `app.manifest`, commits the package,
  pushes a new `<env>-import/` branch, and opens a pull request to `main`. It uses `BUILD_BUILDID`,
  `BUILD_REPOSITORY_ID`, `BUILD_REPOSITORY_NAME`, `SYSTEM_ACCESSTOKEN`, `SYSTEM_COLLECTIONURI`,
  `SYSTEM_TEAMPROJECT`, and `SYSTEM_TEAMPROJECTID`. `--skip-lookups` keeps the `lookups/` folder on `main`.
  `--skip-lookup-backups` leaves out `lookups/lookup_file_backups/`. The compare commands take the same two options
  and remove those folders on both sides.
- `onboard <app> <repo> [--permissions]` creates a repository. It writes the sanitized export to `package/`,
  copies `example/azure-pipelines.yml`, pushes the initial `main` commit, and creates the app pipeline. An empty
  repository name uses the app ID. `--permissions` grants the project Build Service Contribute, Contribute to pull
  requests, and Create tag.

## Repair

- `repair-packages <dir> <out-dir> <conf> <stanzas>` checks that each stanza is on the search head and in the
  package's `default/<conf>.conf`. It writes `<out-dir>/temp` one patch above the highest feed or installed version,
  without those stanzas. It writes `<out-dir>/real` one patch above that, with the package content unchanged. It
  sets `REPAIR_VERSION`. Stanza names are separated by `;`. It reads `SYSTEM_ACCESSTOKEN`.
- `delete-local <dir> <conf> <stanzas>` deletes each stanza's local copy through the search head REST API. A stanza
  with no local copy prints `has no local copy`.
- `repair-check <dir> <conf> <stanzas>` exports the app and fails when a stanza still has a local copy, or is missing.

## ACS setup and REST access

- `install-acs` downloads ACS CLI 2.26.0 for Linux or Windows x64 agents. It verifies its SHA-256 checksum, and
  extracts it to `AGENT_TEMPDIRECTORY`. It prepends that directory to `PATH`, runs `acs version`, adds the selected
  stack, and logs in.
- ACS setup maps the variable-group `ACS_TOKEN` to `STACK_TOKEN`. It runs once per job. Later steps reuse the CLI
  configuration.
- `SPLUNK_SEARCH_HEAD` selects a target search head when it is configured. The REST API commands use
  `SPLUNK_REST_URL`. When no search head is set, they use `https://<SPLUNK_STACK>.splunkcloud.com:8089`.
