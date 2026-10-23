# Bulk pipelines

[Home](/Home) > [Getting started](/Getting-started) > Bulk pipelines

[[_TOC_]]

Create three manual pipelines for ACS bulk install, update, and delete commands.
The `file` parameter is relative to `$(Build.SourcesDirectory)`. For
`private-apps`, select a directory containing app packages. Splunkbase commands
use the splunk.com credentials in `splunk-appinspect`, mapped to
`SPLUNK_USERNAME` and `SPLUNK_PASSWORD` in the ACS step environment.

The selected `splunk-<environment>` deployment environment provides approval.
Select `restart` to run the restart stage after the bulk operation. On the
first run, permit `splunk-appinspect`, the selected `splunk-<environment>`
variable group, and the `splunk-<environment>` deployment environment.

## Step 16: Create Splunk ACS Bulk Install

**Where:** **Pipelines → New pipeline**

**Do:**

1. Select **New pipeline**.
2. Select **Azure Repos Git**.
3. Select the repository that contains the pipeline files.
4. Select **Existing Azure Pipelines YAML file**.
5. Select `/bulk-install/azure-pipelines.yml` as the path.
6. Select **Continue**.
7. Enter `Splunk ACS Bulk Install` as the pipeline name.
8. Select the arrow next to **Save & run**.
9. Select **Save**.
10. Select **Edit**.
11. Select **⋮** (More actions) at the top right.
12. Select **Triggers**.
13. Select the **YAML** tab.
14. In **Default agent pool for YAML**, select the configured pool.
15. Select the arrow next to **Save & queue**.
16. Select **Save**.

**Verify:** The pipeline appears under **Pipelines** with no runs.

## Step 17: Create Splunk ACS Bulk Update

**Where:** **Pipelines → New pipeline**

**Do:**

1. Select **New pipeline**.
2. Select **Azure Repos Git**.
3. Select the repository that contains the pipeline files.
4. Select **Existing Azure Pipelines YAML file**.
5. Select `/bulk-update/azure-pipelines.yml` as the path.
6. Select **Continue**.
7. Enter `Splunk ACS Bulk Update` as the pipeline name.
8. Select the arrow next to **Save & run**.
9. Select **Save**.
10. Select **Edit**.
11. Select **⋮** (More actions) at the top right.
12. Select **Triggers**.
13. Select the **YAML** tab.
14. In **Default agent pool for YAML**, select the configured pool.
15. Select the arrow next to **Save & queue**.
16. Select **Save**.

**Verify:** The pipeline appears under **Pipelines** with no runs.

## Step 18: Create Splunk ACS Bulk Delete

**Where:** **Pipelines → New pipeline**

**Do:**

1. Select **New pipeline**.
2. Select **Azure Repos Git**.
3. Select the repository that contains the pipeline files.
4. Select **Existing Azure Pipelines YAML file**.
5. Select `/bulk-delete/azure-pipelines.yml` as the path.
6. Select **Continue**.
7. Enter `Splunk ACS Bulk Delete` as the pipeline name.
8. Select the arrow next to **Save & run**.
9. Select **Save**.
10. Select **Edit**.
11. Select **⋮** (More actions) at the top right.
12. Select **Triggers**.
13. Select the **YAML** tab.
14. In **Default agent pool for YAML**, select the configured pool.
15. Select the arrow next to **Save & queue**.
16. Select **Save**.

**Verify:** The pipeline appears under **Pipelines** with no runs.

## Type and command

| Action | Type | ACS command |
| --- | --- | --- |
| Install | `indexes` | `acs indexes bulk-create --file <file>` |
| Install | `hec-tokens` | `acs hec-token bulk-create --file <file>` |
| Install | `private-apps` | `acs apps bulk-install private` |
| Install | `splunkbase-apps` | `acs apps bulk-fetch-license` |
| Install | `splunkbase-apps` | `acs apps bulk-install splunkbase` |
| Update | `indexes` | `acs indexes bulk-update --file <file>` |
| Update | `hec-tokens` | `acs hec-token bulk-update --file <file>` |
| Update | `private-apps` | `acs apps bulk-install private` |
| Update | `splunkbase-apps` | `acs apps bulk-update --file <file>` |
| Update | `app-permissions` | `acs permissions apps bulk-update` |
| Delete | `indexes` | `acs indexes bulk-delete --file <file>` |
| Delete | `hec-tokens` | `acs hec-token bulk-delete --file <file>` |
| Delete | `apps` | `acs apps bulk-uninstall --file <file>` |

Commands with JSON input files use `--file <file>`. Private app commands use
`--package-src-dir <file> --acs-legal-ack=Y`. Splunkbase install runs these
commands in order:

```sh
acs apps bulk-fetch-license --file <file> --output-file $(Agent.TempDirectory)/apps.json
acs apps bulk-install splunkbase --file $(Agent.TempDirectory)/apps.json
```

Each bulk command tries every item and prints success and failure counts.

## Input examples

Each JSON example shows the contents of the selected input file.

### Indexes

Create input:

```json
{"indexes":[{"name":"bulk-index-0","datatype":"event","maxDataSizeMB":512}]}
```

Update input contains index objects with the fields to change. Delete input
contains an `indexes` array of names.

### HEC tokens

Create input:

```json
{"hec-tokens":[{"name":"mock-token-1"},{"name":"mock-token-2","defaultIndex":"main"}]}
```

Update input contains token objects with the fields to change. Delete input
contains a `hec-tokens` array of names.

### Private apps

Select a directory of app packages, for example:

```text
packages/
  app-one
  app-two
```

The private app command does not take a JSON file.

### Splunkbase apps

The install input for `bulk-fetch-license` is:

```json
{"apps":[{"id":1620},{"id":1274,"version":"6.0.3"}]}
```

ACS CLI documentation lists `apps bulk-update` without an input example.

### App permissions

```json
{"apps":[{"name":"my_app","perms":{"read":["*"],"write":["sc_admin"]}}]}
```

This input follows the ACS API list shape.

### Apps to delete

```json
{"apps":["my_app","other_app"]}
```

## Related

- [Bulk pipelines](/Pipelines)

---

[< Previous: Restart pipeline setup](/Getting-started/Restart) |
[Next: Repair pipeline setup >](/Getting-started/Repair)
