# Bulk delete pipeline

The bulk delete pipeline deletes indexes, HEC tokens, or apps on a stack. It reads the objects from a JSON file.

The pipeline is named `Splunk ACS Bulk Delete` in [Manual pipelines](/Setup/Manual-pipelines).

> **DANGER: the `apps` type uninstalls each app and deletes ALL of its lookups (CSV files) and local settings.**
> There is no undo. Read [Deploy: DANGER: uninstall](/Pipelines/Deploy#danger-uninstall) first.

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack. Uses `splunk-<environment>` and its approval. |
| `type` | `indexes`, `hec-tokens`, `apps` | none | What to delete. |
| `file` | Path from the repository root | none | JSON input file. |
| `restart` | on, off | off | Restart both search heads at the end, if ACS requires it. |

## Run it

Run the pipeline the same way as the bulk install pipeline. See
[Bulk install: Run it](/Pipelines/Bulk-Install#run-it).

## Commands by type

| Type | ACS command |
| --- | --- |
| `indexes` | `acs indexes bulk-delete --file <file>` |
| `hec-tokens` | `acs hec-token bulk-delete --file <file>` |
| `apps` | `acs apps bulk-uninstall --file <file>` |

## Input files

```text
Apps to delete: {"apps":["my_app","other_app"]}
```

Delete input for indexes and HEC tokens lists the names in an `indexes` or `hec-tokens` array.

Each bulk command tries every item. It prints success and failure counts. The stage that runs the command is
described in [Reference: Stages](/Reference/Stages#bulk-stage). If a command fails with an ACS error, see
[ACS troubleshooting](/Troubleshooting/ACS).
