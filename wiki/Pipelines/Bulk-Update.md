# Bulk update pipeline

The bulk update pipeline updates indexes, HEC tokens, apps, or app permissions on a stack. It reads the
objects from a JSON file, or from a directory for private apps.

The pipeline is named `Splunk ACS Bulk Update` in [Manual pipelines](/Setup/Manual-pipelines).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack. Uses `splunk-<environment>` and its approval. |
| `type` | `indexes`, `hec-tokens`, `private-apps`, `splunkbase-apps`, `app-permissions` | none | What to update. |
| `file` | Path from the repository root | none | JSON input file. For `private-apps`, a directory with one package directory per app. |
| `restart` | on, off | off | Restart both search heads at the end, if ACS requires it. |

## Run it

Run the pipeline the same way as the bulk install pipeline. See
[Bulk install: Run it](/Pipelines/Bulk-Install#run-it).

## Commands by type

| Type | ACS command |
| --- | --- |
| `indexes` | `acs indexes bulk-update --file <file>` |
| `hec-tokens` | `acs hec-token bulk-update --file <file>` |
| `private-apps` | `acs apps bulk-install private --package-src-dir <file> --acs-legal-ack=Y` |
| `splunkbase-apps` | `acs apps bulk-update --file <file>` |
| `app-permissions` | `acs permissions apps bulk-update --file <file>` |

Private apps use the same directory input as the [bulk install](/Pipelines/Bulk-Install#input-files) pipeline.

## Input files

The input for an update lists the objects to change.

```text
App permissions: {"apps":[{"name":"my_app","perms":{"read":["*"],"write":["sc_admin"]}}]}
```

The ACS CLI documentation has no example for `apps bulk-update`.

Each bulk command tries every item. It prints success and failure counts. The stage that runs the command is
described in [Reference: Stages](/Reference/Stages#bulk-stage). If a command fails with an ACS error, see
[ACS troubleshooting](/Troubleshooting/ACS).
