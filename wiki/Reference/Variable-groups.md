# Variable groups

Use this page to find each variable group, its variables and values, and which variables stay locked. This is
the only page that lists the variables. To create the groups, follow [Variable groups setup](/Setup/Variable-groups).

## Groups

| Group | Description | Variables |
| --- | --- | --- |
| `splunk-appinspect` | Splunk.com account for AppInspect and ACS installs, and the app agent pool | `SPLUNK_USERNAME`, `SPLUNK_PASSWORD`, `AGENT_POOL` |
| `splunk-nonprod` | Nonprod Splunk Cloud stack for pull request and main installs | `SPLUNK_STACK`, `ACS_TOKEN` |
| `splunk-prod` | Production Splunk Cloud stack for compare and manual deploy | `SPLUNK_STACK`, `ACS_TOKEN` |
| `splunk-itsi-nonprod` | Nonprod ITSI search head on the Splunk Cloud stack | `SPLUNK_STACK`, `SPLUNK_SEARCH_HEAD`, `ACS_TOKEN` |
| `splunk-itsi-prod` | Production ITSI search head on the Splunk Cloud stack | `SPLUNK_STACK`, `SPLUNK_SEARCH_HEAD`, `ACS_TOKEN` |

## Variables

| Group | Variable | Value | Lock |
| --- | --- | --- | --- |
| `splunk-appinspect` | `SPLUNK_USERNAME` | Username of a splunk.com account | Off |
| `splunk-appinspect` | `SPLUNK_PASSWORD` | Password of the same account | On |
| `splunk-appinspect` | `AGENT_POOL` | Agent pool that Onboard writes into a new app's `azure-pipelines.yml`. Optional | Off |
| `splunk-nonprod` | `SPLUNK_STACK` | `<stack>` from `https://<stack>.splunkcloud.com` | Off |
| `splunk-nonprod` | `ACS_TOKEN` | ACS token for the stack. Empty until the token is created | On |
| `splunk-prod` | `SPLUNK_STACK` | `<stack>` from `https://<stack>.splunkcloud.com` | Off |
| `splunk-prod` | `ACS_TOKEN` | ACS token for the stack. Empty until the token is created | On |
| `splunk-itsi-nonprod` | `SPLUNK_STACK` | Same value as `splunk-nonprod` | Off |
| `splunk-itsi-nonprod` | `SPLUNK_SEARCH_HEAD` | Nonprod ITSI search head name from provisioning information | Off |
| `splunk-itsi-nonprod` | `ACS_TOKEN` | ACS token for the ITSI search head. Empty until created | On |
| `splunk-itsi-prod` | `SPLUNK_STACK` | Same value as `splunk-prod` | Off |
| `splunk-itsi-prod` | `SPLUNK_SEARCH_HEAD` | Prod ITSI search head name from provisioning information | Off |
| `splunk-itsi-prod` | `ACS_TOKEN` | ACS token for the ITSI search head. Empty until created | On |

- The REST URL is built, not entered: `https://<SPLUNK_SEARCH_HEAD>.<SPLUNK_STACK>.splunkcloud.com:8089`, or
  `https://<SPLUNK_STACK>.splunkcloud.com:8089` when no search head is set.
- Scripts read the unlocked variables directly. Locked variables are mapped in the pipeline YAML.

## Pipelines and groups

| Pipeline | Variable groups |
| --- | --- |
| App pipeline | `splunk-appinspect`, `splunk-nonprod`, `splunk-itsi-nonprod`, `splunk-prod`, `splunk-itsi-prod` |
| Deploy and bulk pipelines | `splunk-appinspect` and the selected `splunk-<environment>` |
| Restart | The selected `splunk-<environment>` or `splunk-itsi-<environment>` |
| Repair | `splunk-appinspect` and the selected `splunk-<env>` or `splunk-itsi-<env>` |
| Compare | Source and target groups selected by the `splunk` or `splunk-itsi` prefix |
| Smoke test | `splunk-appinspect` and the selected target groups |
| Onboard | `splunk-appinspect` and the selected `splunk-itsi-<environment>` or `splunk-<environment>` |
| Import | `splunk-itsi-<environment>` |

Bulk Splunkbase commands read `SPLUNK_USERNAME` and `SPLUNK_PASSWORD` from `splunk-appinspect`. The pipeline
maps them into the ACS step environment.

![Groups selected by pipeline and environment.](../diagrams/variable-group-use.png)
