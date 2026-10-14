# Agent setup and network access

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Agent setup and network access

[[_TOC_]]

## Python 3.13 is not available on a self-hosted agent

**Symptom:** `UsePythonVersion@0` cannot find Python 3.13.

**Cause:** The task finds Python versions in the agent tool cache. The required
version is not in `_work/_tool/Python/3.13.x/x64`.

**Fix:**

1. Install Python 3.13 x64 in `_work/_tool/Python/3.13.x/x64` on the agent.
2. Rerun the failed job.

**Docs:** [Use Python version](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## `Unable to locate executable file: 'bash'`

**Symptom:** The job reports `Unable to locate executable file: 'bash'` on a
Windows agent.

**Cause:** The selected agent does not provide the shell expected by the
pipeline task. The YAML uses one command per `script` step. Most commands call
Python; the ACS version step calls `acs version` directly.

**Fix:**

1. Select a Linux agent pool for this pipeline.
2. For compare and smoke-test pipelines, set **Default agent pool for YAML**
   under **Edit → … → Triggers → YAML**.
3. For an app pipeline, set it in the app repo's `pool` template parameter.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters).

## `CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate`

**Symptom:** The ACS CLI download fails certificate verification in `curl`.

**Cause:** HTTPS inspection presents a certificate issuer the agent does not
trust. `curl` uses the operating system certificate store.

**Fix:**

1. Add the HTTPS inspection root certificate to the agent OS trust store.
2. Rerun **Set up ACS CLI 2.26.0**.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## Agent cannot reach a required service

**Symptom:** A download, package install, login, or API request times out or
cannot resolve its service.

**Cause:** The agent cannot make outbound HTTPS requests to a required host.

**Fix:**

1. Allow agent outbound HTTPS to `github.com` for the ACS CLI download.
2. Allow agent outbound HTTPS to `pypi.org` for Python packages.
3. Allow agent outbound HTTPS to `api.splunk.com` for AppInspect login.
4. Allow agent outbound HTTPS to `appinspect.splunk.com` for validation.
5. Allow agent outbound HTTPS to `admin.splunk.com` for ACS requests.
6. Rerun the failed job.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[ACS CLI](https://github.com/splunk/acs-cli).

## Related

- [Permissions](/Troubleshooting/Permissions)

---

[< Previous: Permissions and first run](/Troubleshooting/Permissions) |
[Next: Build troubleshooting >](/Troubleshooting/Build)
