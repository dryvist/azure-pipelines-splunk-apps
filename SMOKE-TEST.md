# Smoke test

One pipeline run checks the AppInspect account, the selected target's nonprod
and prod stack names and ACS tokens, ITSI search head names when selected, and
the `export_apps` capability. ACS jobs run the shared setup before their
check step. See [release.py commands](wiki/Reference/Release.py-commands.md)
for the per-job setup lifecycle. The pipeline only reads and changes no stack.

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
11. Select **Edit**.
12. Select **⋮** (More actions) at the top right.
13. Select **Triggers**.
14. Select the **YAML** tab.
15. In **Default agent pool for YAML**, select your agent pool.
16. Select the arrow next to **Save & queue**.
17. Select **Save**.

## Run it

1. Select **Run pipeline**.
2. Select `splunk` or `splunk-itsi` for `target` in the Run panel.
3. Select **Run**.
4. If the run shows **This pipeline needs permission**, select **View**.
5. Select **Permit** for `splunk-appinspect`.
6. Select **Permit** for the selected nonprod variable group.
7. Select **Permit** for the selected prod variable group.

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

The steps are **Check AppInspect credentials**, **Check nonprod ACS access and
export**, **Check prod ACS access and export**, and **Result**.

| Job | Checks | Variable group |
| --- | --- | --- |
| `appinspect` | AppInspect sign-in works | `splunk-appinspect` |
| `nonprod` | Lists and exports apps | `<target>-nonprod` |
| `prod` | Lists and exports apps | `<target>-prod` |
| `result` | All three jobs succeeded | none |

Success lines in the job logs:

```text
PASS AppInspect login
PASS <target>-nonprod ACS login and app list
PASS <target>-nonprod export_apps: <n> bytes
PASS <target>-prod ACS login and app list
PASS <target>-prod export_apps: <n> bytes
```

## Fix a failure

- `FAIL <group>: empty value for <names>`: fill those variables in that
  group.
- `HTTP 401` or `HTTP 403` from `api.splunk.com`: check the splunk.com user
  name and password.
- `Error:` before the app list line: check `SPLUNK_STACK`, the `acs` token,
  and, for `splunk-itsi`, `SPLUNK_SEARCH_HEAD`.
- `Error:` after the app list line: grant `export_apps` to the token
  account.

The `nonprod` and `prod` jobs export only the local and user files of the
built-in `search` app, which every stack has.
