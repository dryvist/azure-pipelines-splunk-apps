# Smoke-test pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Smoke-test pipeline

[[_TOC_]]

The manual pipeline checks AppInspect credentials and read-only ACS access for
nonprod and prod. It accepts `splunk` or `splunk-itsi` as the `target` value.
The `result` job runs after all three checks, including when a check fails.

The ACS jobs check login, list apps, and export only local and user
configuration files from the built-in `search` app. They do not change a
stack. See [release.py commands](/Reference/Release.py-commands) for the ACS
setup lifecycle.

## Before you run it

Complete Steps 1 to 4 in [Getting started](/Getting-started).

## Create the pipeline

1. Open **Pipelines → Pipelines**.
2. Select **New pipeline**.
3. Select **Azure Repos Git**.
4. Select the repository containing this pipeline.
5. Select **Existing Azure Pipelines YAML file**.
6. Select branch `main`.
7. Select `/smoke-test/azure-pipelines.yml`.
8. Select **Continue**.
9. Select the arrow next to **Run**.
10. Select **Save**.
11. Select **Edit**.
12. Select **⋮** (More actions).
13. Select **Triggers**.
14. Select the **YAML** tab.
15. Select the default agent pool for YAML.
16. Select the arrow next to **Save & queue**.
17. Select **Save**.

**Verify:** Confirm the pipeline uses `/smoke-test/azure-pipelines.yml` and the
intended agent pool.

## Run the pipeline

1. Select **Run pipeline**.
2. Select `splunk` or `splunk-itsi` for `target`.
3. Select **Run**.
4. If the run requests permission, select **View**.
5. Permit `splunk-appinspect`.
6. Permit the selected nonprod variable group.
7. Permit the selected prod variable group.

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

The jobs run these steps and use these variable groups:

| Job | Step | Variable group |
| --- | --- | --- |
| `appinspect` | Check AppInspect credentials | `splunk-appinspect` |
| `nonprod` | Check nonprod ACS access and export | `<target>-nonprod` |
| `prod` | Check prod ACS access and export | `<target>-prod` |
| `result` | Result | none |

The check jobs print `PASS` lines for AppInspect login, ACS login and app
listing, and the `search` export. For failures, use
[Smoke-test troubleshooting](/Troubleshooting/Smoke-test).

## Related

- [Getting started](/Getting-started)
- [Compare pipeline](/Pipelines/Compare-pipeline)
- [Smoke-test troubleshooting](/Troubleshooting/Smoke-test)

---

[< Previous: Restart pipeline](/Pipelines/Restart-pipeline)
