# Environments and ACS access

[Home](/Home) > [Getting started](/Getting-started) > Environments and ACS

[[_TOC_]]

Steps 3 and 4 cover deployment environments, ACS tokens, and export access.

## Step 3: Create deployment environments

**Where:** **Pipelines → Environments**

**Do:**

1. Select **Create environment**.
2. Enter `splunk-nonprod` as the environment name.
3. Create the environment.
4. Select **Create environment**.
5. Enter `splunk-prod` as the environment name.
6. Create the environment.

To require approval before production deployment:

1. Open `splunk-prod`.
2. Go to **Approvals and checks → Approvals → +**.
3. Add the approvers.

**Verify:**

1. Confirm `splunk-nonprod` appears in the environments list.
2. Confirm `splunk-prod` appears in the environments list.
3. If configured, confirm `splunk-prod` shows its approval check.

## Step 4: Create ACS tokens and grant export access

**Where:** In Splunk Web, use **Settings → Tokens** on each stack and its ITSI
search head, and **Settings → Roles** for roles. To enter token values, use
**Pipelines → Library → `<group>`**.

**Do:**

1. In Splunk Web for the nonprod stack, go to **Settings → Tokens**.
2. Create an ACS token for the nonprod stack.
3. Set its audience to `acs`.
4. In Splunk Web on the nonprod ITSI search head, go to **Settings → Tokens**.
5. Create an ACS token on the nonprod ITSI search head.
6. Set its audience to `acs`.
7. In Splunk Web for the prod stack, go to **Settings → Tokens**.
8. Create an ACS token for the prod stack.
9. Set its audience to `acs`.
10. In Splunk Web on the prod ITSI search head, go to **Settings → Tokens**.
11. Create an ACS token on the prod ITSI search head.
12. Set its audience to `acs`.
13. Go to **Pipelines → Library → `splunk-nonprod`**.
14. Enter the nonprod token as the `ACS_TOKEN` value.
15. Go to **Pipelines → Library → `splunk-prod`**.
16. Enter the prod token as the `ACS_TOKEN` value.
17. Go to **Pipelines → Library → `splunk-itsi-nonprod`**.
18. Enter the nonprod ITSI token as the `ACS_TOKEN` value.
19. Go to **Pipelines → Library → `splunk-itsi-prod`**.
20. Enter the prod ITSI token as the `ACS_TOKEN` value.
21. Go to **Settings → Roles**.
22. Open the role for each ACS token account.
23. Confirm the nonprod and prod stack accounts have `install_apps`.
24. Confirm the nonprod and prod stack accounts have `edit_local_apps`.
25. Grant each account the `export_apps` capability.

`sc_admin` can grant the `export_apps` capability to itself.

**Verify:**

1. Confirm the nonprod stack token exists.
2. Confirm the nonprod ITSI search head token exists.
3. Confirm the prod stack token exists.
4. Confirm the prod ITSI search head token exists.
5. Confirm the nonprod and prod stack accounts have `install_apps`.
6. Confirm the nonprod and prod stack accounts have `edit_local_apps`.
7. Confirm all four token accounts have `export_apps`.

## Related

- [Variable groups](/Reference/Variable-groups)

---

[< Previous: Variable groups](/Getting-started/Variable-groups) |
[Next: App repository >](/Getting-started/App-repository)
