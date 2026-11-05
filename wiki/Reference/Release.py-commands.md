# release.py commands

Use this page to look up what each `release.py` command does. Run the commands from the repository root. Pipelines
call them from job steps. Every ACS command retries every 30 seconds for up to 15 minutes while ACS is busy.

In the **Needs** column:

- **ACS** means `SPLUNK_STACK` and `STACK_TOKEN`. The variable group's `ACS_TOKEN` maps to `STACK_TOKEN`. See
  [Variable groups](/Reference/Variable-groups).
- **Azure** means the `SYSTEM_*` and `BUILD_*` variables of a pipeline job, including `SYSTEM_ACCESSTOKEN`.

## Build and package

| Command | What it does | Needs |
| --- | --- | --- |
| `bump` | On pull request runs, compares source and target versions. If equal, bumps above the feed and pushes to the source branch. | Azure |
| `package` | Checks and sorts `package/`, then writes `dist/<app-id>-<version>.tar.gz`. | Nothing |
| `tag` | Pushes a `v<version>` tag and sets `APP_ID` and `APP_VERSION`. | Git push access |
| `stages-succeeded <stage...>` | Fails unless every named stage succeeded in this build. | Azure |
| `feed-missing <app-id>` | Sets `MISSING` to `true` if the feed has no version of the app, else `false`. | Azure |
| `appinspect <dir>` | Submits the first package, saves HTML and JSON reports, and fails if checks do not pass. | `SPLUNK_USERNAME`, `SPLUNK_PASSWORD` |
| `appinspect-json <report>` | Prints the report and lists checks that did not pass. | Nothing |
| `appinspect-link` | Prints this build's artifact link. | Azure |

## Deploy, wait, and restart

| Command | What it does | Needs |
| --- | --- | --- |
| `deploy <dir>` | Installs every `<app-id>-<version>.tar.gz` package as a private app. | ACS |
| `uninstall <dir>` | Removes the listed apps from all search heads, with their lookups and local settings, and waits until gone. | ACS |
| `status` | Prints stack status and warns if a restart is required. | ACS |
| `wait-version <dir>` | Waits until each app has the package version and the stack is ready. | ACS |
| `restart` | Restarts the stack only when required, then waits for the status to clear. | ACS |
| `acs <args...>` | Runs an ACS CLI command with the job's ACS configuration. | ACS |

## Export and compare

| Command | What it does | Needs |
| --- | --- | --- |
| `export <out-dir> [app-id...]` | Exports default, local and user content to `<out-dir>/<app-id>.tgz`. | ACS |
| `tree <target> <source> <out> [flags]` | Lists added, removed and changed raw files, ignoring line endings and trailing spaces. | Nothing |
| `local-diff <target> <source> <out> [flags]` | Compares target local settings (`-`) with source defaults (`+`). | Nothing |
| `data-models <target> <source> <out> [flags]` | Compares merged data model JSON, ignoring formatting-only changes. | Nothing |
| `diff <target> <source> <out> [flags]` | Writes a patch of merged defaults, a merged archive and a summary. | Nothing |

- `export` takes app IDs, `--all`, or a package directory. See [Compare](/Pipelines/Compare#parameters) for the apps ACS
  limits.
- The compare flags are `--reverse`, which swaps the displayed sides, and `--skip-lookups`.
- Compare commands omit install checksums and lookup backups.
- Data models appear in the `diff` summary, not its patch.
- `tree`, `local-diff`, `diff` and `import` sort readable CSV rows. A CSV they cannot read stays as it is and prints a
  warning.

## Onboard and import

| Command | What it does | Needs |
| --- | --- | --- |
| `import <env> <export-dir> [--skip-lookups]` | Merges an export into `package/`, updates its version and manifest, and opens a pull request. | Azure |
| `onboard <app>` | Exports a private installed app into its repository and creates its pipeline. | ACS, Azure, optional `AGENT_POOL` |

Import removes local settings, user files and lookup backups. `--skip-lookups` keeps the repository's `lookups/` folder.

## Repair

`<stanzas>` are names separated by `;`. These commands also read the optional `SPLUNK_SEARCH_HEAD`.

| Command | What it does | Needs |
| --- | --- | --- |
| `repair-packages <dir> <out-dir> <conf> <stanzas>` | Checks the stanzas, writes `temp/` without and `real/` with them, sets `REPAIR_VERSION`. | ACS, Azure |
| `delete-local <dir> <conf> <stanzas>` | Deletes each stanza's local copy through the REST API. | ACS |
| `repair-check <dir> <conf> <stanzas>` | Exports the app and fails if a stanza is missing or still has a local copy. | ACS |
| `saved-searches <action> <apps> <searches> <file> [--write]` | See [Saved searches](/Pipelines/Saved-searches). | Port 8089 |

## ACS setup

| Command | What it does | Needs |
| --- | --- | --- |
| `install-acs` | Downloads and verifies ACS CLI 2.26.0, adds the stack and logs in. Setup runs once per job. | ACS, `AGENT_TEMPDIRECTORY` |

The optional `SPLUNK_SEARCH_HEAD` selects the REST target.
