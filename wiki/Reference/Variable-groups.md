# Variable groups

This page maps each pipeline to its variable groups. It also lists which variables stay locked.

| Pipeline | Variable groups |
| --- | --- |
| App pipeline | `splunk-appinspect`, `splunk-nonprod`, `splunk-itsi-nonprod`, `splunk-prod`, `splunk-itsi-prod` |
| Deploy and bulk pipelines | `splunk-appinspect` and the selected `splunk-<environment>` |
| Restart | Selected `splunk-<environment>` or `splunk-itsi-<environment>` |
| Compare | Source and target groups selected by the `splunk` or `splunk-itsi` prefix |
| Smoke test | `splunk-appinspect` and the selected target groups |
| Import | `splunk-itsi-<environment>` |

Bulk Splunkbase commands read `SPLUNK_USERNAME` and `SPLUNK_PASSWORD` from `splunk-appinspect`. The pipeline maps them into the ACS step environment.

Keep `SPLUNK_USERNAME`, `SPLUNK_STACK`, and `SPLUNK_SEARCH_HEAD` unlocked. Scripts read them directly.

Keep `SPLUNK_PASSWORD` and `ACS_TOKEN` locked. Map them in YAML.

![Groups selected by pipeline and environment.](../diagrams/variable-group-use.png)

To create the groups, follow [Variable groups setup](/Getting-started/Variable-groups).
