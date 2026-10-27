# Bulk pipelines setup

Create the three manual pipelines that run ACS bulk install, update, and delete.

| Pipeline name | YAML path |
| --- | --- |
| `Splunk ACS Bulk Install` | `/bulk-install/azure-pipelines.yml` |
| `Splunk ACS Bulk Update` | `/bulk-update/azure-pipelines.yml` |
| `Splunk ACS Bulk Delete` | `/bulk-delete/azure-pipelines.yml` |

For each row, follow [Manual pipeline setup](/Getting-started/Manual-pipeline).

On the first run, permit these resources when asked:

- `splunk-appinspect`
- The selected `splunk-<environment>` variable group
- The `splunk-<environment>` deployment environment

If a request does not match, use [Permissions troubleshooting](/Troubleshooting/Permissions).

## Run inputs

- **environment:** `nonprod` or `prod`. The selected `splunk-<environment>` deployment environment provides approval.
- **type:** The resource type. Pick a value from the action table below.
- **file:** The input JSON file, or a directory of app packages for `private-apps`. Relative to `$(Build.SourcesDirectory)`.
- **restart:** Select to restart both search heads at the end, if ACS requires it.

Splunkbase commands use the splunk.com credentials in `splunk-appinspect`, mapped to `SPLUNK_USERNAME` and `SPLUNK_PASSWORD`.

## Actions

| Action | Type | ACS command |
| --- | --- | --- |
| Install | `indexes` | `acs indexes bulk-create --file <file>` |
| Install | `hec-tokens` | `acs hec-token bulk-create --file <file>` |
| Install | `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| Install | `splunkbase-apps` | Run the two commands below. |
| Update | `indexes` | `acs indexes bulk-update --file <file>` |
| Update | `hec-tokens` | `acs hec-token bulk-update --file <file>` |
| Update | `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| Update | `splunkbase-apps` | `acs apps bulk-update --file <file>` |
| Update | `app-permissions` | `acs permissions apps bulk-update --file <file>` |
| Delete | `indexes` | `acs indexes bulk-delete --file <file>` |
| Delete | `hec-tokens` | `acs hec-token bulk-delete --file <file>` |
| Delete | `apps` | `acs apps bulk-uninstall --file <file>` |

To install Splunkbase apps, run these commands in order:

```sh
acs apps bulk-fetch-license --file <file> --output-file $(Agent.TempDirectory)/apps.json
acs apps bulk-install splunkbase --file $(Agent.TempDirectory)/apps.json
```

Each bulk command tries every item. It prints success and failure counts.

## Input files

```text
Indexes, create:     {"indexes":[{"name":"bulk-index-0","datatype":"event","maxDataSizeMB":512}]}
HEC tokens, create:  {"hec-tokens":[{"name":"mock-token-1"},{"name":"mock-token-2","defaultIndex":"main"}]}
Splunkbase, install: {"apps":[{"id":1620},{"id":1274,"version":"6.0.3"}]}
App permissions:     {"apps":[{"name":"my_app","perms":{"read":["*"],"write":["sc_admin"]}}]}
Apps to delete:      {"apps":["my_app","other_app"]}
```

Update input lists the objects to change. Delete input for indexes and HEC tokens lists the names in an
`indexes` or `hec-tokens` array. The ACS CLI documentation has no example for `apps bulk-update`.

Private apps take no JSON file. Select a directory with one package directory per app.

If a bulk command fails with an ACS error, use [Nonprod troubleshooting](/Troubleshooting/Nonprod).
