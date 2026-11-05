# Saved searches pipeline

The saved searches pipeline disables or enables the shared scheduled saved searches in chosen apps, on one search
head. It leaves private searches, unscheduled reports and other apps alone.

The pipeline is named `saved-searches` in [Manual pipelines](/Setup/Manual-pipelines). It uses the search head REST
API on port 8089, so the caller's public IP must be on the stack's `search-api` IP allow list. Until the agents have
a fixed IP on that list, [run it from a workstation](#run-it-from-a-workstation).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to change. The change stage waits for the `splunk-<environment>` approval. |
| `target` | `splunk`, `splunk-itsi` | `splunk` | `splunk` uses `splunk-<env>`, the main search head. `splunk-itsi` uses `splunk-itsi-<env>`. |
| `action` | `disable`, `enable` | `disable` | What to do with each search. |
| `apps` | App IDs separated by `;` | none | Such as the list from a Deploy run. |
| `searches` | `all`, or names separated by `;` | `all` | Limits the run to these searches. |

Each search prints one timestamped line: `DISABLE <app>/<search>` in the plan, `DISABLED` in the change, or
`ALREADY DISABLED`. The last line is `Result`. A rerun skips searches that are already done. The
`saved-searches-plan` and `saved-searches-before-change` artifacts hold each search's state before the run.

## Run it

1. Open the saved searches pipeline.
2. Select **Run pipeline**.
3. Set `environment`, `target`, `action` and `apps`.
4. Select **Run**.
5. Open the **Plan to disable the shared scheduled searches (read-only)** step.
6. Confirm it lists only the searches you expect.
7. Select **disable on `<target>-<environment>` (optional, run by hand)**.
8. Select **Run stage**.
9. Approve the `splunk-<environment>` check.
10. Confirm the step's last line is `Result: <n> disabled`.

## Run it from a workstation

The same command runs on any Windows machine with Python 3.11 or later. These steps use PowerShell.

1. Run `curl.exe -s https://api.ipify.org` to print your public IP.
2. In Splunk Web of the stack, select **Settings → Server settings → IP allow list**.
3. Select **Search head API access**.
4. Add `<your IP>/32`.
5. Select **Save**.
6. Wait 5 minutes for Splunk Cloud to apply it.
7. Run `cd <your clone of azure-pipelines-splunk-apps>`.
8. Run `python -m pip install --quiet splunk-sdk==2.1.0`.
9. Run `$env:SPLUNK_STACK = "<stack>"`.
10. Run `$env:SPLUNK_SEARCH_HEAD = ""` for the main search head, or set the ITSI search head name.
11. Run `$t = Read-Host "ACS token" -AsSecureString`, then paste the token.
12. Run `$env:STACK_TOKEN = [Net.NetworkCredential]::new('', $t).Password`.
13. Run `python release.py saved-searches disable "app_one;app_two" all plan.json`.
14. Confirm the plan lists only the searches you expect.
15. Run `python release.py saved-searches disable "app_one;app_two" all before-change.json --write`.
16. Confirm the last line is `Result: <n> disabled`.
17. Run `Remove-Item Env:STACK_TOKEN`.
18. Remove `<your IP>/32` from **Search head API access**, using steps 2 to 5.

Keep `before-change.json`. It lists each search and whether it was disabled before the change.
