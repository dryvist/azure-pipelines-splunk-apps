# Agent setup and network access

Use this page to fix missing tools, certificate errors, and blocked services on agents.

## Python 3.13 is not available on a self-hosted agent

**Symptom:** `UsePythonVersion@0` cannot find Python 3.13.

**Fix:**

1. Install Python 3.13 x64 in `_work/_tool/Python/3.13.x/x64` on the agent.
2. Rerun the failed job.

**Docs:** [Use Python version](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## `python is not on PATH on agent <agent>`

**Symptom:** **Use Python 3.13** succeeds, then **Use UTF-8 for Python files and output** fails with this message.
Self-hosted agents never download Python.

**Fix:**

1. On the named agent, restart the Azure Pipelines agent Windows service. The agent reads PATH only when the
   service starts, so a Python install or upgrade since the last start can leave PATH out of date.
2. Rerun the failed job.
3. If it fails again, open **Use Python 3.13** and note the folder it adds to PATH.
4. On the agent, install Python 3.13 into that tool cache folder. Run this in an elevated PowerShell, with the
   agent's tool cache path:

   ~~~powershell
   $v = "3.13.3"; $tc = "<agent folder>\_work\_tool\Python\$v"
   Invoke-WebRequest "https://www.python.org/ftp/python/$v/python-$v-amd64.exe" -OutFile "$env:TEMP\py.exe"
   Start-Process "$env:TEMP\py.exe" -Wait -ArgumentList "/quiet InstallAllUsers=1 PrependPath=0 Include_test=0 TargetDir=$tc\x64"
   New-Item -ItemType File -Force "$tc\x64.complete" | Out-Null
   & "$tc\x64\python.exe" --version
   ~~~

5. Rerun the failed job.

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
