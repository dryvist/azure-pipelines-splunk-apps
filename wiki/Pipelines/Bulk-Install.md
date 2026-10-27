# Bulk install pipeline

The bulk install pipeline installs indexes, HEC tokens, private apps, or Splunkbase apps on a stack. It reads
the objects from a JSON file, or from a directory for private apps.

The pipeline is named `Splunk ACS Bulk Install` in [Manual pipelines](/Setup/Manual-pipelines).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack. Uses `splunk-<environment>` and its approval. |
| `type` | `indexes`, `hec-tokens`, `private-apps`, `splunkbase-apps` | none | What to install. |
| `file` | Path from the repository root | none | JSON input file. For `private-apps`, a directory with one package directory per app. |
| `restart` | on, off | off | Restart both search heads at the end, if ACS requires it. |

## Run it

1. Open the bulk install pipeline and select **Run pipeline**.
2. Select the `environment` and the `type`.
3. Enter `file`.
4. Select `restart` if the stack should restart at the end when ACS requires it.
5. Select **Run**.
6. Permit the requested resources. A first run usually asks for `splunk-appinspect`, the selected
   `splunk-<environment>` group, and the `splunk-<environment>` environment. See
   [Permissions](/Troubleshooting/Permissions).

## Commands by type

| Type | ACS command |
| --- | --- |
| `indexes` | `acs indexes bulk-create --file <file>` |
| `hec-tokens` | `acs hec-token bulk-create --file <file>` |
| `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| `splunkbase-apps` | Two commands, shown below |

To install Splunkbase apps, the pipeline runs these two commands in order:

```sh
acs apps bulk-fetch-license --file <file> --output-file $(Agent.TempDirectory)/apps.json
acs apps bulk-install splunkbase --file $(Agent.TempDirectory)/apps.json
```

The Splunkbase commands use the splunk.com account from `splunk-appinspect`. See
[Reference: Stages](/Reference/Stages#bulk-stage).

## Input files

```text
Indexes, create:     {"indexes":[{"name":"bulk-index-0","datatype":"event","maxDataSizeMB":512}]}
HEC tokens, create:  {"hec-tokens":[{"name":"mock-token-1"},{"name":"mock-token-2","defaultIndex":"main"}]}
Splunkbase, install: {"apps":[{"id":1620},{"id":1274,"version":"6.0.3"}]}
```

Private apps take no JSON file. Select a directory with one package directory per app.

Each bulk command tries every item. It prints success and failure counts. The stage that runs the command is
described in [Reference: Stages](/Reference/Stages#bulk-stage). If a command fails with an ACS error, see
[ACS troubleshooting](/Troubleshooting/ACS).
