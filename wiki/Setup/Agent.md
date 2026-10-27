# Agent

One time. Done at project setup; you should not need this again.

Prepare the Azure agents that run the pipelines. The agents need Python 3.13, outbound network access, and an
allow list entry for their addresses.

## Python 3.13

Azure agents must have Python 3.13 available in the UsePythonVersion tool cache. If it is missing, see
[Agent setup troubleshooting](/Troubleshooting/Agent-setup).

## Outbound HTTPS

Allow agent outbound HTTPS to these hosts:

- `pypi.org`, for Python packages.
- `api.splunk.com`, for the AppInspect login.
- `appinspect.splunk.com`, for AppInspect validation.
- `admin.splunk.com`, for ACS requests.
- `github.com`, for the ACS CLI download.

## Allow lists for agent addresses

Add the agents' outbound addresses to both lists below.

1. Add the addresses to the `acs` feature allowlist. This list covers ACS requests.
2. Add the addresses to the `search-api` feature allowlist. In Splunk Web of the nonprod stack, select
   **Settings → Server settings → IP allow list**. Select **Search head API access**, add the agent's public IP
   address, and select **Save**.
3. Repeat step 2 in Splunk Web of the prod stack.

Verify that both stacks list the agent's address under **Search head API access**.
