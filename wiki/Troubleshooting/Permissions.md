# Permissions and first run

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Permissions and first run

[[_TOC_]]

## Before the first stage

### Variable group not found or not authorized

**Symptom:** `Variable group  was not found`, a named group was not found, or
the run says **This pipeline needs permission**.

**Cause:** Group names must match the pipeline reference exactly. These
pipelines use hyphens, such as `splunk-appinspect`, not underscores. The
pipeline may also lack permission to use a group or environment.

**Fix:**

1. Compare each requested group name with the names in
   **Pipelines → Library**.
2. Rename any group that uses underscores to the exact hyphenated name.
3. Select **View** in the permission banner.
4. Select **Permit** for each requested variable group.
5. Select **Permit** for each requested deployment environment.
6. If no banner appears, add the pipeline under each group's **Pipeline
   permissions**.
7. If no banner appears, add the pipeline under each environment's
   **Security → Pipeline permissions**.

**Docs:** [Variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups),
[environments](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments),
[approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals).

### `A template expression is not allowed in this context` for `pool`

**Symptom:** Pipeline validation rejects the `pool` template expression.

**Cause:** The shared template sets `pool` from its `pool` parameter. A pool
must also be selected in the pipeline settings for pipelines that do not
extend that template.

**Fix:**

1. Open the pipeline and select **Edit**.
2. Select **… → Triggers → YAML**.
3. Set **Default agent pool for YAML**.
4. In an app repo, set the `pool` value under the template's `parameters`.

**Docs:** [Runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters),
[expressions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## Related

- [Agent setup](/Troubleshooting/Agent-setup)

---

[Next: Agent setup and network access >](/Troubleshooting/Agent-setup)
