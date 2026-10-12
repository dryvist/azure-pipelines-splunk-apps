# One-click smoke test

This manually run pipeline checks AppInspect login and ACS access for the
nonprod and prod stacks. Its ACS requests use `GET` and make no stack changes.

| Job | Proves | Needs |
| --- | --- | --- |
| `appinspect` | AppInspect login | `splunk-appinspect` |
| `nonprod` | ACS app list | `splunk-nonprod` |
| `prod` | ACS app list and `search` export | `splunk-prod`, `export_apps` |

The `splunk-appinspect` variable group needs `SPLUNK_USERNAME` and secret
`SPLUNK_PASSWORD`. Each ACS variable group needs `SPLUNK_STACK` and secret
`ACS_TOKEN`. Allow the pipeline to use all three variable groups.

## Create and run

1. Open **Pipelines** and select **New pipeline**.
2. Select **Azure Repos Git**.
3. Select `azure-pipelines-splunk-apps`.
4. Select **Existing Azure Pipelines YAML file**.
5. Choose branch `smoke-test` and path
   `/smoke-test/azure-pipelines.yml`.
6. Select **Continue**, then select **Run**.

## Read the result

All three jobs must be green. Their logs show these lines on success:

```text
PASS AppInspect login
PASS nonprod ACS: <n> apps
PASS prod ACS: <n> apps
PASS prod export_apps: <n> bytes
```

The ACS app list response uses the `apps` field. The count is the number of
entries returned by the list request.

## Fix failures

- `401` or `403` on AppInspect login: check the username and password.
- `401` or `403` on an ACS list: check the token and its ACS audience.
- `404` on an ACS list: check the exact `SPLUNK_STACK` name.
- `403` on prod export: the prod account needs the `export_apps` capability.

A failed request logs `HTTP <status> from <url>` and the response body.
