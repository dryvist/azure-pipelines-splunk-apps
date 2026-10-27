# Package feed

Create the package feed and grant publish access to the Build Service.

## Step 1: Create the package feed

**Where:** **Artifacts → Create Feed**

**Do:**

1. Select the project scope for the feed.
2. Enter `splunk-apps` as the feed name.
3. Create the feed.
4. Open **Feed settings → Permissions**.
5. Add `<project> Build Service (<org>)`.
6. Set its role to **Feed Publisher (Contributor)**.

**Verify:**

1. Confirm `splunk-apps` appears in Artifacts.
2. Confirm the Build Service is listed as a Feed Publisher (Contributor).

If the release cannot publish, use [Release troubleshooting](/Troubleshooting/Release).
