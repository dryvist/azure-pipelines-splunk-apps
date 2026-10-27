# Smoke-test pipeline

Use this page to create and run the pipeline that checks AppInspect credentials and read-only ACS access for nonprod and prod.

The `target` value is `splunk` or `splunk-itsi`. The `result` job runs after the three checks, including when a check fails.

Complete setup steps 1 to 4 in [Getting started](/Getting-started) before you run this pipeline.

The ACS jobs check login, list apps, and export only local and user
configuration files from the built-in `search` app. They do not change a
stack. See [release.py commands](/Reference/Release.py-commands) for the ACS
setup lifecycle.

## Create the pipeline

| Pipeline name | YAML path |
| --- | --- |
| `smoke-test` | `/smoke-test/azure-pipelines.yml` |

Create it with [Manual pipeline setup](/Getting-started/Manual-pipeline).

## Run the pipeline

1. Select **Run pipeline**.
2. Select `splunk` or `splunk-itsi` for `target`.
3. Select **Run**.
4. Permit requested resources using [Permissions troubleshooting](/Troubleshooting/Permissions).

**Verify:** Confirm the `appinspect`, `nonprod`, `prod`, and `result` jobs
finish.

## Read the result

1. Open the run.
2. Open the `result` job.
3. Select the **Result** step.
4. Read its last line:

```text
RESULT: ALL PASS
RESULT: FAILED - open each failed job for its FAIL or Error line
```

The jobs run these checks:

| Job | Check |
| --- | --- |
| `appinspect` | AppInspect credentials |
| `nonprod` | Nonprod ACS access and export |
| `prod` | Prod ACS access and export |
| `result` | Job results |

The check jobs print `PASS` for login, app listing, and export. See [Variable groups](/Reference/Variable-groups) for the groups selected by `target`.

If a check fails, use [Smoke-test troubleshooting](/Troubleshooting/Smoke-test).
