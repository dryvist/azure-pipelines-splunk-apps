# Release setup

[Home](/Home) > [Getting started](/Getting-started) > Release setup

[[_TOC_]]

Step 11 checks the first release after merge.

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

## Related

- [Release stage](/Stages/Release)

---

[< Previous: App pipeline setup](/Getting-started/App-pipeline) |
[Next: Manual deploy setup >](/Getting-started/Manual-deploy)
