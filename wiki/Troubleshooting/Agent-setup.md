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

## One host always times out while others work

**Symptom:** Every run times out on one host, such as `<stack>.splunkcloud.com` on port 8089, with no HTTP status.
Other hosts on the same domain work from the same agent. `Test-NetConnection <host> -Port 8089` shows
`TcpTestSucceeded : False`.

**Cause:** Something on the agent or its network sends that one host name or address the wrong way. The examples
below use the sample addresses `198.51.100.10` for the failing host and `203.0.113.20` for a working one.

**Fix:** Run each check in PowerShell on an agent machine. Stop at the first one that finds something.

| # | What can break one host | Check |
| --- | --- | --- |
| 1 | A `hosts` file entry for the host name | `Select-String -Path C:\Windows\System32\drivers\etc\hosts -Pattern splunkcloud` |
| 2 | Internal DNS returns another address | `Resolve-DnsName <host>`, then `Resolve-DnsName <host> -Server 8.8.8.8`; they should match |
| 3 | A name resolution policy (NRPT) from group policy | `Get-DnsClientNrptPolicy` |
| 4 | A stale DNS cache | `Clear-DnsClientCache`, then test again |
| 5 | A Windows Firewall outbound block rule | See the command below the table |
| 6 | A static route for that address | `Find-NetRoute -RemoteIPAddress 198.51.100.10`; compare the gateway with `Find-NetRoute -RemoteIPAddress 203.0.113.20` |
| 7 | An endpoint security block on the address or URL | Ask the security team to search their block list for the host and address |
| 8 | Agent proxy settings | `netsh winhttp show proxy`, and the `.proxy` and `.proxybypass` files in the agent folder |

Check 5 lists the outbound block rules that name an address:

```powershell
Get-NetFirewallRule -Direction Outbound -Action Block -Enabled True | Get-NetFirewallAddressFilter |
  Where-Object RemoteAddress -ne Any
```

If the agents run in Azure, ask the cloud team to check these for the agent subnet:

- Network security group outbound rules that deny the address or port.
- Azure Firewall rules, when the subnet routes through one.
- Route tables with a route that covers the address.
- Private DNS zones linked to the virtual network for `splunkcloud.com`. A record there overrides public DNS, like check 2.

If every check is clean, give the network team the agent public IP, the host and its address from the warning. Ask
them to check the egress firewall logs for that address and port. If traffic leaves and gets no reply, open a Splunk
support case with the same details.

**Docs:** [Test-NetConnection](https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection),
[Resolve-DnsName](https://learn.microsoft.com/en-us/powershell/module/dnsclient/resolve-dnsname).
