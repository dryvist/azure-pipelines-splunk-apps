# Import from nonprod

[Home](/Home) > [Pipelines](/Pipelines) > Import from nonprod

[[_TOC_]]

The import option exports the installed app from the nonprod ITSI search head,
compares it with the app package from `main`, and opens a pull request in the
app repository. It uses the `splunk-itsi-nonprod` variable group. It does not
install the package in nonprod.

## Run the import

1. Open **Pipelines → Pipelines → `<pipeline>`**.
2. Select **Run pipeline**.
3. Select `main` as the branch.
4. Select **Import this app from nonprod into a new pull request**.
5. Select **Run**.

## Import stage

1. **Checkout app:** Gets the app repository at `main` and keeps credentials
   for the branch push.
2. **Checkout tools:** Gets the shared release scripts.
3. **Select Python:** Selects the configured Python version.
4. **Install diff dependencies:** Installs pinned `ksconf` and Splunk SDK
   packages.
5. **Install packaging toolkit:** Installs the `slim` package command.
6. **Package main app:** Builds the app package in `app/dist`.
7. **Set up ACS CLI:** Adds the nonprod stack with the ITSI search head as the
   target and authenticates with ACS.
8. **Check stack status before deploy:** Reports the nonprod stack status.
9. **Export this app from nonprod via ACS:** Writes the export to
   `nonprod-export/<app-id>/` and sets `APP_ID`.
10. **Compare nonprod with this package (file tree, local and default):**
   Writes raw file changes to the diff output.
11. **Compare nonprod with this package (local files vs default):**
   Writes the local-versus-default report.
12. **Compare nonprod with this package (merged defaults):** Writes the patch,
   summary, HTML report, and merged archive.
13. **Publish diff artifact:** Publishes
    `nonprod-diff-<app-id>-<attempt>`.
14. **Open a pull request with the nonprod app:** Merges local configuration
    into default, removes `local/`, `users/`, and `metadata/local.meta`, sets
    both app version rows to one patch above `main`, and regenerates
    `app.manifest`. It sets `acceleration = false` in `datamodels.conf` and
    `action.populate_lookup = 0` in `savedsearches.conf`, with one warning per
    stanza, because Splunk Cloud AppInspect rejects them when on. The stack
    keeps its own `local/` values, so an acceleration turned on in Splunk Web
    stays on after a deploy.

The import commit uses a new branch named
`nonprod-import/<version>-<Build.BuildId>` and opens a pull request to `main`.
Each run creates a new branch and pull request. The pull request validation run
skips the automatic version bump because the imported version differs from
`main`.

Review the diff artifact before changing the pull request. Edit the pull
request to choose what to keep, or close it to discard the import.

## Related

- [App pipeline](/Pipelines/App-pipeline)
- [Nonprod stage](/Stages/Nonprod)
- [release.py commands](/Reference/Release.py-commands)

---

[< Previous: App pipeline](/Pipelines/App-pipeline) |
[Next: Deploy pipeline >](/Pipelines/Deploy-pipeline)
