# Bulk pipelines

Use these pipelines to install, update or delete indexes, HEC tokens and apps on a stack, or to update app permissions.

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Selects the stack and deployment environment; prod waits for approval. |
| `type` | The types in [Actions](#actions) for that pipeline | none | Selects the object type. |
| `file` | Path relative to `Build.SourcesDirectory` | none | JSON input file; `private-apps` uses a directory with one package directory per app. |
| `restart` | `true`, `false` | `false` | Run a restart stage after the bulk action if ACS requires it. |

## Run it

1. Open **Pipelines**.
2. Open the pipeline from the [Actions](#actions) table.
3. Select **Run pipeline**.
4. Set `environment`.
5. Select `type`.
6. Enter the path for `file`.
7. Set `restart` to `true` or `false`.
8. Select **Run**.
9. Permit the `splunk-appinspect` variable group if prompted.
10. Permit the selected environment variable group if prompted.
11. Approve the selected deployment environment if prompted. See [Permissions](/Troubleshooting/Permissions).

## Actions

| Pipeline name | Type | ACS command |
| --- | --- | --- |
| `Splunk ACS Bulk Install` | `indexes` | `acs indexes bulk-create --file <file>` |
| `Splunk ACS Bulk Install` | `hec-tokens` | `acs hec-token bulk-create --file <file>` |
| `Splunk ACS Bulk Install` | `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| `Splunk ACS Bulk Install` | `splunkbase-apps` | `acs apps bulk-fetch-license --file <file>`, then `acs apps bulk-install splunkbase` on its output |
| `Splunk ACS Bulk Update` | `indexes` | `acs indexes bulk-update --file <file>` |
| `Splunk ACS Bulk Update` | `hec-tokens` | `acs hec-token bulk-update --file <file>` |
| `Splunk ACS Bulk Update` | `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| `Splunk ACS Bulk Update` | `splunkbase-apps` | `acs apps bulk-update --file <file>` |
| `Splunk ACS Bulk Update` | `app-permissions` | `acs permissions apps bulk-update --file <file>` |
| `Splunk ACS Bulk Delete` | `indexes` | `acs indexes bulk-delete --file <file>` |
| `Splunk ACS Bulk Delete` | `hec-tokens` | `acs hec-token bulk-delete --file <file>` |
| `Splunk ACS Bulk Delete` | `apps` | `acs apps bulk-uninstall --file <file>` |

> **DANGER:** The `apps` delete type uninstalls each app and permanently deletes all its lookups (CSV files) and local
> settings. There is no undo. Read [Deploy: DANGER: uninstall](/Pipelines/Deploy#danger-uninstall) first.

## Input files

```text
Indexes, create:     {"indexes":[{"name":"bulk-index-0","datatype":"event","maxDataSizeMB":512}]}
HEC tokens, create:  {"hec-tokens":[{"name":"mock-token-1"},{"name":"mock-token-2","defaultIndex":"main"}]}
Splunkbase, install: {"apps":[{"id":1620},{"id":1274,"version":"6.0.3"}]}
App permissions:     {"apps":[{"name":"my_app","perms":{"read":["*"],"write":["sc_admin"]}}]}
Apps to delete:      {"apps":["my_app","other_app"]}
```

- Delete input for indexes and HEC tokens lists names in an `indexes` or `hec-tokens` array.
- Private apps use a directory, not a JSON file.
- Splunkbase installs use the splunk.com account from `splunk-appinspect`.
- Each ACS bulk command tries every item and reports success and failure counts.

See [Bulk stage](/Reference/Stages#bulk-stage) for stage behavior and [ACS troubleshooting](/Troubleshooting/ACS) for
ACS errors.
