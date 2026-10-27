# Package feed

One time. Done at project setup; you should not need this again.

Create the `splunk-apps` package feed. Let the Build Service publish packages to it.

1. Open **Artifacts**, then select **Create Feed**.
2. Select the project scope for the feed.
3. Enter `splunk-apps` as the feed name, then create the feed.
4. Open **Feed settings → Permissions**.
5. Add `<project> Build Service (<org>)`.
6. Set its role to **Feed Publisher (Contributor)**.

Verify:

1. Confirm `splunk-apps` appears in **Artifacts**.
2. Confirm the Build Service is listed as **Feed Publisher (Contributor)**.

If a release cannot publish, see [Release troubleshooting](/Troubleshooting/Release).
