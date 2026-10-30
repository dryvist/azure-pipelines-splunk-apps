# AppInspect troubleshooting

Use this page to fix AppInspect login, package, and validation failures.

## `KeyError: 'SPLUNK_USERNAME'`

**Symptom:** `Run AppInspect` exits with `KeyError: 'SPLUNK_USERNAME'`.

**Fix:**

1. Add `SPLUNK_USERNAME` to `splunk-appinspect`. See [Variable groups](/Setup/Variable-groups).
2. Set its lock state as listed in [Reference: Variable groups](/Reference/Variable-groups).
3. Rerun the `appinspect` job.

## `Expected one .tar.gz package`

**Symptom:** `Run AppInspect` or a deploy step prints `Expected one .tar.gz package in <dir>, found <count>`.

**Fix:**

1. Open the `dist` artifact, or the selected feed package directory.
2. Confirm it contains exactly one `.tar.gz` package.
3. Rerun the build or deployment after correcting the package contents.

**Docs:** [Artifacts](/Reference/Artifacts),
[Pipeline artifacts](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts).

## AppInspect login returns 401 or 403

**Symptom:** The log shows `HTTP 401` or `HTTP 403` from the AppInspect login request to `api.splunk.com`.

**Fix:**

1. Set `SPLUNK_USERNAME` to the account username in `splunk-appinspect`.
2. Set `SPLUNK_PASSWORD` to that account's password.
3. Set the variable lock states as listed in [Reference: Variable groups](/Reference/Variable-groups).
4. Rerun the `appinspect` job.

**Docs:** [AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[secret variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables).

## AppInspect does not pass

**Symptom:** The log prints `AppInspect did not pass`. The **Blocks deployment** section shows a status other
than `SUCCESS`, or a count above 0.

**Fix:**

1. Open **Show AppInspect JSON report** in the failed job. Red lines are failures and errors. The list at the
   end names each check that did not pass.
2. Open the link from **Show AppInspect HTML report link**.
3. Open `appinspect-report-<attempt>` for the failed job attempt.
4. Fix each reported finding in the app.
5. Rerun validation after fixing the findings.

For the pass criteria, see [Reference: Stages](/Reference/Stages#appinspect). For report names, see
[Artifacts](/Reference/Artifacts).
