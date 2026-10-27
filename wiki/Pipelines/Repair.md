# Repair pipeline

The repair pipeline removes the local copies of chosen objects in one app. After that, the app's default
copies apply again.

The pipeline is named `repair-app-objects` in [Manual pipelines](/Setup/Manual-pipelines). Before the first
run, set up REST access as described in [Variable groups](/Setup/Variable-groups) and
[Agent](/Setup/Agent).

## Parameters

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `environment` | `nonprod`, `prod` | `nonprod` | Stack to repair. The stage waits for the `splunk-<environment>` approval. |
| `target` | `splunk`, `splunk-itsi` | `splunk` | `splunk` uses `splunk-<env>`. `splunk-itsi` uses `splunk-itsi-<env>`. |
| `app` | App ID | none | App to repair, such as `my_ta`. |
| `conf` | Configuration file name | none | Without `.conf`, such as `savedsearches`. |
| `stanzas` | Stanza names separated by `;` | none | Such as `Search one;Search two`. |

## Run it

1. Open the repair pipeline and select **Run pipeline**.
2. Select the environment and the target.
3. Enter `app`, `conf`, and `stanzas`.
4. Select **Run**.
5. When the stage waits, approve the `splunk-<environment>` check. Permit any requested resource. See
   [Permissions](/Troubleshooting/Permissions).

## Versions

A new install must have a higher version than the installed app. The pipeline takes the highest version
among the splunk-apps feed and the installed app.

- The temporary package is that version plus one patch. The pipeline never publishes it.
- The real package is that version plus two patches. It has the same content as the latest feed package.
  The pipeline publishes it to the splunk-apps feed.
- The next version bump in the app pipeline goes above the highest feed version. The next release therefore
  installs over the repaired app.

## What happens

1. **Check `<app-id>` is in the splunk-apps feed** and **Download `<app-id>` from the splunk-apps feed** get
   the latest package. These steps are described in [Deploy: Package steps](/Pipelines/Deploy#package-steps).
2. **Set up ACS CLI** prepares the ACS session for the selected group.
3. **Check the stanzas, then build the temporary and real packages** fails before any install when a stanza
   is not on the search head, or not in the package's `default/<conf>.conf`. It prints the installed,
   temporary, and real versions.
4. **Install on `<environment>`** and **Check the installed version** install the temporary package.
5. **Delete the local copies via the REST API** deletes each stanza's local copy. A stanza with no local copy
   prints `has no local copy`.
6. **Publish the real package to the splunk-apps feed.**
7. **Install on `<environment>`** and **Check the installed version** install the real package.
8. **Check the stanzas now come from default only** exports the app. It fails when a stanza still has a local
   copy or is missing.

Between steps 4 and 7, the objects exist only as local copies. After step 5, they do not exist at all. If the
run fails after step 5, run the [Deploy pipeline](/Pipelines/Deploy) to install the latest feed package.

## REST access

Steps 3, 5, and 8 call the search head REST API on port 8089, with the group's `ACS_TOKEN`. The agent's IP
address must be on the stack's search-api IP allow list. The REST URL rule is in
[Reference: Variable groups](/Reference/Variable-groups).
