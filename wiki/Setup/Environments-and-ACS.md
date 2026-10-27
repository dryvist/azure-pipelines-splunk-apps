# Environments and ACS

One time. Done at project setup; you should not need this again.

Create the two deployment environments and their checks. Then create an ACS token for each stack and each ITSI
search head.

## Deployment environments

1. Open **Pipelines → Environments**. Select **Create environment**.
2. Enter `splunk-nonprod` as the environment name. Select **Create**.
3. Select **Create environment**. Enter `splunk-prod` as the environment name. Select **Create**.
4. Open `splunk-prod`. Select **Approvals and checks**, then **+**, then **Approvals**.
5. Add the approvers. Set **Timeout** to `12 hours`. Select **Create**.
6. Select **+**, then **Exclusive Lock**, then **Create**.
7. Open `splunk-nonprod`. Select **Approvals and checks**, then **+**, then **Exclusive Lock**, then **Create**.

Verify:

1. `splunk-prod` shows an **Approvals** check with a **Timeout** of `12 hours`.
2. `splunk-prod` shows an **Exclusive Lock** check.
3. `splunk-nonprod` shows an **Exclusive Lock** check.

## ACS tokens

Create one token for each row. Enter it in the variable group in the same row.

| Create the token in | Enter it in variable group |
| --- | --- |
| Splunk Web for the nonprod stack | `splunk-nonprod` |
| Splunk Web for the nonprod ITSI search head | `splunk-itsi-nonprod` |
| Splunk Web for the prod stack | `splunk-prod` |
| Splunk Web for the prod ITSI search head | `splunk-itsi-prod` |

1. In Splunk Web for the row's stack or search head, select **Settings → Tokens**.
2. Create an ACS token. Set its audience to `acs`.
3. In Azure, select **Pipelines → Library** and open the row's variable group. Set `ACS_TOKEN` to the token
   value, then select **Save**.
4. Repeat for each row.

## Account capabilities

| Token account | Required capabilities |
| --- | --- |
| Nonprod and prod stack accounts | `install_apps`, `edit_local_apps`, `export_apps` |
| Nonprod and prod ITSI search head accounts | `export_apps` |

1. In Splunk Web, select **Settings → Roles**.
2. Open the role for each ACS token account.
3. Grant the capabilities in the table.

The `sc_admin` role can grant the `export_apps` capability to itself.

If a token is rejected, see [ACS troubleshooting](/Troubleshooting/ACS).
