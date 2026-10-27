# Agent setup and network access

Use this page to fix missing tools, certificate errors, and blocked services on agents.

## Python 3.13 is not available on a self-hosted agent

**Symptom:** `UsePythonVersion@0` cannot find Python 3.13.

**Fix:**

1. Install Python 3.13 x64 in `_work/_tool/Python/3.13.x/x64` on the agent.
2. Rerun the failed job.

**Docs:** [Use Python version](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## `Unable to locate executable file: 'bash'`

**Symptom:** A job step reports `Unable to locate executable file: 'bash'`.

**Fix:**

1. Confirm the run uses the expected branch and shared templates.
2. Check the expanded job for an explicit Bash task from another template.
3. Use a configured agent shell. Keep this repository's steps as one Python command or a built-in task.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters).

## `CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate`

**Symptom:** The ACS CLI download fails certificate verification in `curl`.

**Fix:**

1. Add the HTTPS inspection root certificate to the agent OS trust store.
2. Rerun **Set up ACS CLI 2.26.0**.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## Agent cannot reach a required service

**Symptom:** A download, package install, login, or API request times out, or cannot resolve its service.

**Fix:**

1. Allow the outbound HTTPS hosts listed in [Agent](/Setup/Agent#outbound-https).
2. Rerun the failed job.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[ACS CLI](https://github.com/splunk/acs-cli).
