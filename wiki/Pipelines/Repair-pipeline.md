# Repair pipeline

Use this page to see the repair pipeline inputs and job order.

## Behavior

The manual repair pipeline in `repair/azure-pipelines.yml` removes the local
copies of chosen objects in one app, so the app's default copies apply again.
Splunk does not let the REST API delete an object that the app's `default/`
folder also defines. The pipeline first installs a temporary version of the app
without those objects, deletes the local copies, then installs the real app
again.

Run form parameters:

- **Environment:** `nonprod` or `prod`.
- **Variable groups:** `splunk` uses `splunk-<env>`; `splunk-itsi` uses
  `splunk-itsi-<env>`.
- **App ID:** the app to repair, such as `my_ta`.
- **Configuration file name without .conf:** such as `savedsearches`.
- **Stanza names, separated by ;:** such as `Search one;Search two`.

The stage waits for the `splunk-<env>` approval before any step runs.

## Versions

Splunk Cloud installs only a higher version of an installed private app. The
pipeline takes the highest version among the splunk-apps feed and the installed
app:

- The temporary package is that version plus one patch. It is never published.
- The real package is that version plus two patches. It has the same content as
  the latest feed package. The pipeline publishes it to the splunk-apps feed.

The app pipeline's version bump always goes above the highest feed version, so
the next release installs over the repaired app.

## Steps

1. **Check `<app-id>` is in the splunk-apps feed** and **Download `<app-id>`
   from the splunk-apps feed:** get the latest package.
2. **Set up ACS CLI:** prepares the ACS session for the selected group.
3. **Check the stanzas, then build the temporary and real packages:** fails
   before any install when a stanza is not on the search head or not in the
   package's `default/<conf>.conf`. It prints the installed, temporary and real
   versions.
4. **Install on `<environment>`** and **Check the installed version:** install
   the temporary package.
5. **Delete the local copies via the REST API:** deletes each stanza's local
   copy. A stanza with no local copy prints `has no local copy`.
6. **Publish the real package to the splunk-apps feed.**
7. **Install on `<environment>`** and **Check the installed version:** install
   the real package.
8. **Check the stanzas now come from default only:** exports the app and fails
   when a stanza still has a local copy or is missing.

Between steps 4 and 7, the objects exist only as local copies, then not at all.
If the run fails after step 5, run the
[Deploy pipeline](/Pipelines/Deploy-pipeline) to install the latest feed
package.

## REST API access

Step 3, step 5 and step 8 call the search head REST API on port 8089 with the
group's `ACS_TOKEN`. The agent's IP address must be on the stack's
`search-api` IP allow list. Without `SPLUNK_SEARCH_HEAD`, the URL is
`https://<SPLUNK_STACK>.splunkcloud.com:8089`. A group with
`SPLUNK_SEARCH_HEAD` needs `SPLUNK_REST_URL` set to that search head's URL. See
[Repair pipeline setup](/Getting-started/Repair).
