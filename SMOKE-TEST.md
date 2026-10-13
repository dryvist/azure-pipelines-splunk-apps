# Smoke test

One pipeline run checks every external value the release pipeline needs:
the AppInspect account, both Splunk Cloud stack names, both ACS tokens and
the `export_apps` capability on both stacks. It only reads. It changes
nothing on any Splunk stack.

## Before you run it

Complete Steps 1 to 4 of `AZURE-DEVOPS-SETUP.md`.

## Create the pipeline

1. Go to **Pipelines → Pipelines**.
2. Select **New pipeline**.
3. Select **Azure Repos Git**.
4. Select `azure-pipelines-splunk-apps`.
5. Select **Existing Azure Pipelines YAML file**.
6. Select branch `main`.
7. Select path `/smoke-test/azure-pipelines.yml`.
8. Select **Continue**.
9. Select the arrow next to **Run**.
10. Select **Save**.

## Run it

1. Select **Run pipeline**.
2. Select **Run**.
3. If the run shows **This pipeline needs permission**, select **View**.
4. Select **Permit** for `splunk-appinspect`.
5. Select **Permit** for `splunk-nonprod`.
6. Select **Permit** for `splunk-prod`.

## Read the result

1. Open the run.
2. Select the job named `result`.
3. Select its `Result` step.
4. Read the last line. It is one of:

```text
RESULT: ALL PASS
RESULT: FAILED - open each failed job for its FAIL or Error line
```

## What each job checks

| Job | Checks | Variable group |
| --- | --- | --- |
| `appinspect` | AppInspect sign-in works | `splunk-appinspect` |
| `nonprod` | Token and stack name can list and export apps | `splunk-nonprod` |
| `prod` | Token and stack name can list and export apps | `splunk-prod` |
| `result` | All three jobs succeeded | none |

Success lines in the job logs:

```text
PASS AppInspect login
PASS splunk-nonprod ACS login and app list
PASS splunk-nonprod export_apps: <n> bytes
PASS splunk-prod ACS login and app list
PASS splunk-prod export_apps: <n> bytes
```

## Fix a failure

- `FAIL <group>: empty value for <names>`: fill those variables in that
  group.
- `HTTP 401` or `HTTP 403` from `api.splunk.com`: check the splunk.com user
  name and password.
- `Error:` before the app list line: check `SPLUNK_STACK` and the `acs`
  token.
- `Error:` after the app list line: grant `export_apps` to the token
  account.

The `nonprod` and `prod` jobs export only the local and user files of the
built-in `search` app, which every stack has.
