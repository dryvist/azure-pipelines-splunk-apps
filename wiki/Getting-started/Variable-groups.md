# Variable groups

[Home](/Home) > [Getting started](/Getting-started) > Variable groups

[[_TOC_]]

Step 2 creates the variable groups. The
[reference matrix](/Reference/Variable-groups) shows which pipelines use
each group.

## Step 2: Create the variable groups

**Where:** **Pipelines → Library → + Variable group**

**Do:**

Create the `splunk-appinspect` group:

1. Select **+ Variable group**.
2. Type `splunk-appinspect` as the group name.
3. Type `Splunk.com account for AppInspect validation and ACS installs` as
   the description.
4. Add a variable.
5. Type `SPLUNK_USERNAME` as the variable name.
6. Type the username of a splunk.com account as its value.
7. Set its lock icon off. Do not lock `SPLUNK_USERNAME`; locked variables
   are not passed to scripts unless mapped.
8. Add a variable.
9. Type `SPLUNK_PASSWORD` as the variable name.
10. Type the password of the same splunk.com account as its value.
11. Set its lock icon on.

`SPLUNK_USERNAME` is sourced from the account used to sign in at splunk.com
and Splunkbase. `appinspect`, `nonprod`, and the manual deploy pipeline use
its AppInspect token as proof of validation. `SPLUNK_PASSWORD` is used by the
same steps as `SPLUNK_USERNAME`.

Create the `splunk-nonprod` group:

1. Select **+ Variable group**.
2. Type `splunk-nonprod` as the group name.
3. Type `Nonprod Splunk Cloud stack for pull request and main installs` as the
description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the nonprod stack name as its value. It is the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
7. Set its lock icon off. Do not lock `SPLUNK_STACK`; locked variables are
    not passed to scripts unless mapped.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until [Step 4](/Getting-started/Environments-and-ACS).
11. Set its lock icon on.

`SPLUNK_STACK` is used by `nonprod`. The `ACS_TOKEN` value is a Splunk Cloud
authentication token with audience `acs`, sourced from Splunk Web on the
nonprod stack in [Step 4](/Getting-started/Environments-and-ACS) and used by
`nonprod`.

Create the `splunk-prod` group:

1. Select **+ Variable group**.
2. Type `splunk-prod` as the group name.
3. Type `Production Splunk Cloud stack for compare and manual deploy` as the
description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the production stack name as its value. It is the `<stack>` part of
    `https://<stack>.splunkcloud.com`.
7. Set its lock icon off. Do not lock `SPLUNK_STACK`; locked variables are
    not passed to scripts unless mapped.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until [Step 4](/Getting-started/Environments-and-ACS).
11. Set its lock icon on.

The prod `SPLUNK_STACK` is used by `proddiff` and the manual deploy pipeline.
The prod `ACS_TOKEN` value is a Splunk Cloud authentication token with
audience `acs`; its account needs `export_apps`, `install_apps` and
`edit_local_apps`. The token is sourced from Splunk Web on the production
stack in [Step 4](/Getting-started/Environments-and-ACS).

Create the `splunk-itsi-nonprod` group:

1. Select **+ Variable group**.
2. Type `splunk-itsi-nonprod` as the group name.
3. Type `Nonprod ITSI search head on the Splunk Cloud stack` as the
   description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the nonprod stack name as its value.
7. Set its lock icon off.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until [Step 4](/Getting-started/Environments-and-ACS).
11. Set its lock icon on.
12. Add a variable.
13. Type `SPLUNK_SEARCH_HEAD` as the variable name.
14. Type the nonprod ITSI search head name from provisioning information.
15. Set its lock icon off.

Create the `splunk-itsi-prod` group:

1. Select **+ Variable group**.
2. Type `splunk-itsi-prod` as the group name.
3. Type `Production ITSI search head on the Splunk Cloud stack` as the
   description.
4. Add a variable.
5. Type `SPLUNK_STACK` as the variable name.
6. Type the production stack name as its value.
7. Set its lock icon off.
8. Add a variable.
9. Type `ACS_TOKEN` as the variable name.
10. Leave its value empty until [Step 4](/Getting-started/Environments-and-ACS).
11. Set its lock icon on.
12. Add a variable.
13. Type `SPLUNK_SEARCH_HEAD` as the variable name.
14. Type the prod ITSI search head name from provisioning information.
15. Set its lock icon off.

The ITSI groups use the same `SPLUNK_STACK` value as the matching standard
group. Their `SPLUNK_SEARCH_HEAD` value selects the target search head. The
compare and smoke-test pipelines, the app import, and the app pipeline's prod
compare use the ITSI groups. App
deployments use `splunk-nonprod` or `splunk-prod`.

**Verify:**

1. Confirm the group names are exactly `splunk-appinspect`, `splunk-nonprod`,
   `splunk-prod`, `splunk-itsi-nonprod`, and `splunk-itsi-prod`.
2. Confirm all five groups appear in Library.
3. Confirm secret values are masked after they are saved.

## Related

- [Variable groups](/Reference/Variable-groups)

---

[< Previous: Package feed](/Getting-started/Feed) |
[Next: Environments and ACS access >](/Getting-started/Environments-and-ACS)
