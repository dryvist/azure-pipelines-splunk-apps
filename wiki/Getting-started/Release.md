# Release setup

Check the first package publication and version tag after merging an app pull request.

## Step 11: Check the first release after merging

**Where:** **Repos → Tags** and **Artifacts → splunk-apps**

**Do:**

1. Merge the validated pull request into `main`.
2. Open the main pipeline run.
3. Confirm `build` passes.
4. Confirm `appinspect` passes.
5. Confirm `release` passes.
6. Go to **Repos → Tags**.
7. Find `v<version>`.
8. Go to **Artifacts → splunk-apps**.
9. Find the package named with the lowercase app id and version from
   `app.conf`.

**Verify:**

1. Confirm the tag points to the release commit.
2. Confirm the feed contains the matching Universal Package version.

If the tag or package is missing, use [Release troubleshooting](/Troubleshooting/Release).
