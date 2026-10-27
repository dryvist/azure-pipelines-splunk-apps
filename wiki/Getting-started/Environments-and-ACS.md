# Environments and ACS access

Create the two deployment environments. Then create an ACS token for each stack and ITSI search head.

## Create the deployment environments

1. Open **Pipelines → Environments**.
2. Select **Create environment**.
3. Enter `splunk-nonprod` as the environment name.
4. Select **Create**.
5. Select **Create environment**.
6. Enter `splunk-prod` as the environment name.
7. Select **Create**.
8. Open `splunk-prod`.
9. Select **Approvals and checks**.
10. Select **+**.
11. Select **Approvals**.
12. Add the approvers.
13. Set **Timeout** to `12 hours`.
14. Select **Create**.
15. Select **+**.
16. Select **Exclusive Lock**.
17. Select **Create**.
18. Open `splunk-nonprod`.
19. Select **Approvals and checks**.
20. Select **+**.
21. Select **Exclusive Lock**.
22. Select **Create**.

**Verify:**

1. `splunk-prod` shows an **Approvals** check with a **Timeout** of `12 hours`.
2. `splunk-prod` shows an **Exclusive Lock** check.
3. `splunk-nonprod` shows an **Exclusive Lock** check.

## Create the ACS tokens

Create one token for each row. Enter it in the variable group in the same row.

| Create the token in | Enter it in variable group |
| --- | --- |
| Splunk Web for the nonprod stack | `splunk-nonprod` |
| Splunk Web for the nonprod ITSI search head | `splunk-itsi-nonprod` |
| Splunk Web for the prod stack | `splunk-prod` |
| Splunk Web for the prod ITSI search head | `splunk-itsi-prod` |

1. In Splunk Web for the row's stack or search head, select **Settings → Tokens**.
2. Create an ACS token.
3. Set its audience to `acs`.
4. Select **Pipelines → Library**.
5. Open the row's variable group.
6. Set `ACS_TOKEN` to the token value.
7. Select **Save**.
8. Repeat steps 1 to 7 for each row.

## Grant account capabilities

| Token account | Required capabilities |
| --- | --- |
| Nonprod and prod stack accounts | `install_apps`, `edit_local_apps`, `export_apps` |
| Nonprod and prod ITSI search head accounts | `export_apps` |

1. Select **Settings → Roles**.
2. Open the role for each ACS token account.
3. Grant the capabilities in the table.

`sc_admin` can grant the `export_apps` capability to itself.

For the pipeline-to-group mapping, see [Variable groups](/Reference/Variable-groups).

If a token is rejected, use [Nonprod troubleshooting](/Troubleshooting/Nonprod).
