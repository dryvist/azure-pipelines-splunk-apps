# App pipeline

The app pipeline builds and checks one app. It deploys the app to nonprod and prod. It can also import
installed changes into a pull request.

Each app repository has `package/` and an `azure-pipelines.yml`. That file extends the shared template.
The template defaults to Python 3.13. An app repository can override `setup` and `pool`. `pool` picks the
agent pool, which defaults to `ubuntu-latest`.

## Runs

| Run | Starts when | Stages |
| --- | --- | --- |
| Pull request | A pull request targets `main` | Build, AppInspect, Compare with nonprod, Deploy to nonprod, Compare with prod |
| Main | A commit reaches `main` | The same stages as a pull request, then Release and Deploy to prod |
| Import | You run the pipeline on `main` with an import option | Import from nonprod, Import from prod, or both |

- Pull request runs start from a Build validation policy on `main`. Azure Repos ignores YAML `pr:`
  triggers. The policy is set up in [Onboard, after onboarding](/Pipelines/Onboard#after-onboarding).
- Main runs start from the YAML trigger on `main`.
- **Show stage plan** in the build job prints the run reason and the condition of each stage.
- Stage inputs and outputs are in [Reference: Stages](/Reference/Stages).

![Pull request flow.](../diagrams/pr-run.png)

![Main branch flow.](../diagrams/main-run.png)

## Import

The import options export the installed app from the nonprod or prod ITSI search head. They compare it
with the app package on `main`, then open a pull request. Neither option installs the package. Each
option uses its `splunk-itsi-<env>` variable group.

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `importFromNonprod` | on, off | off | Adds the `import_nonprod` stage. It exports from nonprod and opens a pull request. |
| `importFromProd` | on, off | off | Adds the `import_prod` stage. It exports from prod and opens a pull request. |
| `skipLookups` | on, off | on | Leaves `lookups/` out of both sides. The pull request keeps the lookups on `main`. |

An app repository whose `azure-pipelines.yml` has no `skipLookups` parameter always skips lookups. One
without `importFromProd` shows no prod option.

Imports and compares always leave out `lookups/lookup_file_backups/`. An import removes them from the app.

### Run an import

1. Open **Pipelines**, then open the app pipeline.
2. Select **Run pipeline**.
3. Select `main` as the branch.
4. Select **Import this app from nonprod into a new pull request**, **Import this app from prod into a new
   pull request**, or both. Each selected option makes its own import stage and pull request.
5. To import lookups too, clear **When importing, skip lookups (CSV files) and keep the ones on main**.
6. Select **Run**.
7. Open the `<env>-diff-<app-id>-<attempt>` artifact and review it. Edit the pull request to choose what to
   keep, or close it to discard the import.

Each run creates a new branch named `<env>-import/<version>-<Build.BuildId>` and a new pull request. The
pull request is set to auto-complete and to delete its branch once its policies pass. Its validation run
skips the automatic version bump, because the imported version differs from `main`.

### What the import stage does

The stage is named `import_<env>`, where `<env>` is `nonprod` or `prod`.

1. Gets the app at `main` and the tools repository. Sets up Python, and installs `ksconf`, the Splunk SDK,
   and `slim`.
2. Packages the `main` app into `app/dist`.
3. Sets up the ACS CLI for `<env>`, with the ITSI search head as the target. Reports the stack status.
4. Exports the app to `<env>-export/<app-id>/` and sets `APP_ID`.
5. Compares the export with the `main` package in the four compare steps in
   [Reference: Stages](/Reference/Stages#compare-steps). The steps run in reverse. Lines with `-` are the
   package on `main`. Lines with `+` are `<env>`, the changes the import brings in. Each data model prints
   in its own collapsed group.
6. Publishes `<env>-diff-<app-id>-<attempt>`.
7. Opens the pull request. It merges local configuration into default and removes `local/`, `users/`, and
   `metadata/local.meta`. It sets both app version rows to one patch above the highest version on `main` or
   in the splunk-apps feed. It regenerates `app.manifest`. It sets `acceleration = false` in
   `datamodels.conf` and removes `action.populate_lookup` from `savedsearches.conf`, with one warning per
   stanza. In `app.conf`, it sets the settings Splunk Cloud AppInspect requires, with one warning each:
   - `[id] name` and `[package] id` are the app ID.
   - `[id] version` and `[launcher] version` match the higher of the two. They default to `1.0.0`.
   - `[package] check_for_updates = false`.
   - `[ui] label` is 5 to 80 characters. It defaults to the app ID.
   - `[install] is_configured = true` becomes `false`. `install_source_checksum`,
     `install_source_local_checksum`, and `state_change_requires_restart` are removed.

   Onboard, every package step, and every pull request bump set the same `app.conf` settings.
8. The stack keeps its own `local/` values. An acceleration turned on in Splunk Web stays on after a deploy.

## Check a run

| Stage or job | Expected result |
| --- | --- |
| `build` | Succeeds and publishes `dist`. |
| `appinspect` | Succeeds. Failure, error, and manual check counts are 0. |
| `nonproddiff` | Shows **Compare with nonprod**. Both jobs finish without installing. |
| `nonprod` | Shows **Deploy to nonprod** and installs the package. |
| `proddiff` | Shows **Compare with prod**. Both jobs finish without installing. |

1. Open the pipeline run and check each row in the table.
2. In the `appinspect` job, open the **Show AppInspect HTML report link** step and select the link.
3. Open the `appinspect-report-<attempt>` artifact with the highest attempt number. Download
   `appinspect-report.html` and open it in a browser.

The **Show AppInspect JSON report** step prints the full report. A `future_failure` count above 0 shows a
warning. If the app is not in prod yet, the export log shows `NOT INSTALLED <app-id>`, and every package
file shows as added.

A finished run has the `dist`, `appinspect-report-1`, and `prod-diff-<app-id>-1` artifacts. Their contents
are in [Reference: Artifacts](/Reference/Artifacts).

## Check a release

1. Merge the validated pull request into `main`.
2. Open the main pipeline run. Confirm `build`, `appinspect`, and `release` pass.
3. Open **Repos → Tags** and find `v<version>`. Confirm the tag points to the release commit.
4. Open **Artifacts → splunk-apps** and find the package named with the lowercase app ID and the version
   from `app.conf`. Confirm the feed contains that Universal Package version.

If the tag or package is missing, see [Release troubleshooting](/Troubleshooting/Release).

## Approve the prod install

On a `main` run, **Deploy to prod** does not start by itself. An approval for **Compare with prod** does not
start it.

1. Wait for **Release** and **Compare with prod** to succeed.
2. Open the run.
3. On the **Deploy to prod** stage, select **Run stage**.
4. Approve the `splunk-prod` check as described in [Deploy: Approve a stage](/Pipelines/Deploy#approve-a-stage).

To skip the prod install, do not select **Run stage**.

If a stage skips or fails, see [Build troubleshooting](/Troubleshooting/Build).
