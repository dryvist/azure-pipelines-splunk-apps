# Variable groups

One time. Done at project setup; you should not need this again.

Create the five variable groups that the pipelines read. The group names, descriptions, variables, values,
and lock states are in [Reference: Variable groups](/Reference/Variable-groups).

1. Select **Pipelines → Library → + Variable group**.
2. Enter the group name and the description from the first table in the reference.
3. Select **Add**. Enter the variable name and value from the second table. Set its lock state as listed there.
4. Repeat step 3 for each other variable in the group.
5. Select **Save**.
6. Repeat steps 1 to 5 for each group.
7. After you create the ACS tokens, enter each `ACS_TOKEN` value. See
   [Environments and ACS](/Setup/Environments-and-ACS).
8. For `splunk-itsi-nonprod` and `splunk-itsi-prod`, add the variable `SPLUNK_REST_URL`. Set its value to the
   search head REST URL, such as `https://<host>.splunkcloud.com:8089`. Set its lock icon off, then select
   **Save**. Repeat this for any other group that sets `SPLUNK_SEARCH_HEAD`.

Verify:

1. Confirm each group name matches the reference exactly.
2. Confirm all five groups appear in **Pipelines → Library**.
3. Confirm secret values are masked after saving.
4. Confirm each group with `SPLUNK_SEARCH_HEAD` also has `SPLUNK_REST_URL`.

If a group is missing or denied, see [Permissions](/Troubleshooting/Permissions).
