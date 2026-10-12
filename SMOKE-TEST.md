# Smoke test

One pipeline run checks every external value the release pipeline needs:
the AppInspect account, both Splunk Cloud stack names, both ACS tokens and
the production `export_apps` capability. It only reads. It changes nothing on
any Splunk stack.

## Before you run it

Complete Steps 1 to 5 of `AZURE-DEVOPS-SETUP.md` on the `main` branch:
shared repository, feed, three variable groups with values, environments and
ACS tokens.

## Run it

1. **Pipelines → New pipeline**.
2. **Azure Repos Git** → `azure-pipelines-splunk-apps`.
3. **Existing Azure Pipelines YAML file**.
4. Branch: `smoke-test`. Path: `/smoke-test/azure-pipelines.yml`.
5. **Continue** → **Run**.
6. If the run shows **This pipeline needs permission**, select **View** →
   **Permit** for each variable group.

## Read the result

Open the run. Select the job named `result`, then its `Result` step. The last
line is one of:

```text
RESULT: ALL PASS
RESULT: FAILED - open each failed job for its FAIL or HTTP line
```

Report the `RESULT` line. For a failure, also report the failed job name
and its last line.

## What each job checks

| Job | Checks | Variable group |
| --- | --- | --- |
| `appinspect` | AppInspect sign-in works | `splunk-appinspect` |
| `nonprod` | Token and stack name can list apps | `splunk-nonprod` |
| `prod` | Token and stack name can list and export apps | `splunk-prod` |
| `result` | All three jobs succeeded | none |

Success lines in the job logs:

```text
PASS AppInspect login
PASS nonprod ACS: <n> apps
PASS prod ACS: <n> apps
PASS prod export_apps: <n> bytes
```

## Fix a failure

- `FAIL <group>: empty value for <names>`: fill those variables in that
  group.
- `HTTP 401` or `HTTP 403` from `api.splunk.com`: check the splunk.com user
  name and password.
- `HTTP 401` or `HTTP 403` on an app list: check the ACS token and its `acs`
  audience.
- `HTTP 404` on an app list: check the `SPLUNK_STACK` name.
- `HTTP 403` on `export/download`: grant `export_apps` to the prod token's
  account.

The `prod` job exports only the local and user files of the built-in `search`
app, which every stack has.
