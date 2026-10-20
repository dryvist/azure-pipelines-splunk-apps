# Import from nonprod or prod

[Home](/Home) > [Pipelines](/Pipelines) > Import from nonprod or prod

[[_TOC_]]

The import options export the installed app from the nonprod or prod ITSI
search head, compare it with the app package from `main`, and open a pull
request in the app repository. Each uses its `splunk-itsi-<env>` variable
group. Neither installs the package. Below, `<env>` is `nonprod` or `prod`.

## Run the import

1. Open **Pipelines → Pipelines → `<pipeline>`**.
2. Select **Run pipeline**.
3. Select `main` as the branch.
4. Select **Import this app from nonprod into a new pull request**, or
   **Import this app from prod into a new pull request**. With both selected,
   the run has one import stage and one pull request for each.
5. To import lookups too, clear **When importing, skip lookups (CSV files) and
   keep the ones on main**.
6. To import Splunk lookup backups too, clear **When importing, skip Splunk
   lookup backups (lookups/lookup_file_backups)**.
7. Select **Run**.

With the skip lookups option selected (the default), the compare steps leave
out `lookups/` on both sides and the pull request keeps the lookups on `main`.
An app repository whose `azure-pipelines.yml` has no `skipLookups` parameter
always skips lookups. One without `importFromProd` shows no prod option.

With the skip lookup backups option selected (the default), the compare steps
leave out `lookups/lookup_file_backups/` on both sides and the pull request
does not add the exported backups. An app repository whose
`azure-pipelines.yml` has no `skipLookupBackups` parameter always skips them.

## Import stage

The stage is named `import_<env>`.

1. **Checkout app:** Gets the app repository at `main` and keeps credentials
   for the branch push.
2. **Checkout tools:** Gets the shared release scripts.
3. **Select Python:** Selects the configured Python version.
4. **Install diff dependencies:** Installs pinned `ksconf` and Splunk SDK
   packages.
5. **Install packaging toolkit:** Installs the `slim` package command.
6. **Package main app:** Builds the app package in `app/dist`.
7. **Set up ACS CLI:** Adds the `<env>` stack with the ITSI search head as the
   target and authenticates with ACS.
8. **Check stack status before deploy:** Reports the `<env>` stack status.
9. **Export this app from `<env>` via ACS:** Writes the export to
   `<env>-export/<app-id>/` and sets `APP_ID`.
10. **Compare `<env>` with this package (file tree, local and default):**
   Writes raw file changes to the diff output.
11. **Compare `<env>` with this package (local files vs default):**
   Writes the local-versus-default report.
12. **Compare `<env>` with this package (merged defaults):** Writes the patch,
   summary, HTML report, and merged archive.
13. **Compare `<env>` with this package (data models):** Prints each changed
    data model in its own collapsed group. Steps 10 to 13 run with
    `--reverse`: lines with `-` are the package on `main` and lines with `+`
    are `<env>`, the changes the import brings in.
14. **Publish diff artifact:** Publishes
    `<env>-diff-<app-id>-<attempt>`.
15. **Open a pull request with the `<env>` app:** Merges local configuration
    into default, removes `local/`, `users/`, and `metadata/local.meta`, sets
    both app version rows to one patch above `main`, and regenerates
    `app.manifest`. It sets `acceleration = false` in `datamodels.conf` and
    removes `action.populate_lookup` from `savedsearches.conf`, with one warning
    per stanza, because Splunk Cloud AppInspect rejects them. The stack
    keeps its own `local/` values, so an acceleration turned on in Splunk Web
    stays on after a deploy.

The import commit uses a new branch named
`<env>-import/<version>-<Build.BuildId>` and opens a pull request to `main`.
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
