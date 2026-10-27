# Variable groups

Create the five variable groups with the names, descriptions, and variables in the tables below.

| Group | Description |
| --- | --- |
| `splunk-appinspect` | `Splunk.com account for AppInspect validation and ACS installs` |
| `splunk-nonprod` | `Nonprod Splunk Cloud stack for pull request and main installs` |
| `splunk-prod` | `Production Splunk Cloud stack for compare and manual deploy` |
| `splunk-itsi-nonprod` | `Nonprod ITSI search head on the Splunk Cloud stack` |
| `splunk-itsi-prod` | `Production ITSI search head on the Splunk Cloud stack` |

| Group | Variable | Value |
| --- | --- | --- |
| `splunk-appinspect` | `SPLUNK_USERNAME` | Username of a splunk.com account |
| `splunk-appinspect` | `SPLUNK_PASSWORD` | Password of the same account |
| `splunk-nonprod` | `SPLUNK_STACK` | `<stack>` from `https://<stack>.splunkcloud.com` |
| `splunk-nonprod` | `ACS_TOKEN` | Leave empty for now |
| `splunk-prod` | `SPLUNK_STACK` | `<stack>` from `https://<stack>.splunkcloud.com` |
| `splunk-prod` | `ACS_TOKEN` | Leave empty for now |
| `splunk-itsi-nonprod` | `SPLUNK_STACK` | Same value as `splunk-nonprod` |
| `splunk-itsi-nonprod` | `SPLUNK_SEARCH_HEAD` | Nonprod ITSI search head name from provisioning information |
| `splunk-itsi-nonprod` | `ACS_TOKEN` | Leave empty for now |
| `splunk-itsi-prod` | `SPLUNK_STACK` | Same value as `splunk-prod` |
| `splunk-itsi-prod` | `SPLUNK_SEARCH_HEAD` | Prod ITSI search head name from provisioning information |
| `splunk-itsi-prod` | `ACS_TOKEN` | Leave empty for now |

## Create each group

1. Select **Pipelines → Library → + Variable group**.
2. Enter the group name from the first table.
3. Enter the description from the first table.
4. Select **Add**.
5. Enter the variable name and value from the second table.
6. Set the lock icon as listed in [Reference: Variable groups](/Reference/Variable-groups).
7. Repeat steps 4 to 6 for each other variable in the group.
8. Select **Save**.
9. Repeat steps 1 to 8 for each group.

After you create the ACS tokens, enter each `ACS_TOKEN` value. See [Environments and ACS access](/Getting-started/Environments-and-ACS).

## Verify

1. Confirm each group name matches the table exactly.
2. Confirm all five groups appear in **Pipelines → Library**.
3. Confirm secret values are masked after saving.

If a group is missing or denied, use [Permissions troubleshooting](/Troubleshooting/Permissions).
