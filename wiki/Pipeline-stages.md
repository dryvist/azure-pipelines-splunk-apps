# Pipeline stages

[[_TOC_]]

The `target` parameter selects `splunk` or `splunk-itsi`. Its default is
`splunk`. Variable group and environment names use `<target>-nonprod` and
`<target>-prod`.

## build

- **When:** Pull request validation and runs triggered by commits to `main`.
- **Needs:** The app repo, shared tools repo, Python 3.13, and
  `splunk-packaging-toolkit`.
- **Does:** On pull requests, bumps matching app versions and regenerates
  `app.manifest` when the target version has not changed. Then packages the app.
- **Leaves:** The `dist` artifact with `<app-id>-<version>.tar.gz`, under
  **Artifacts** in the pipeline run.

## appinspect

- **When:** After `build` succeeds for a pull request or a main run.
- **Needs:** The `dist` artifact, `splunk-appinspect`, and the AppInspect API.
- **Does:** Submits the package, polls the `private_victoria` and `future`
  results, and passes only for `SUCCESS` with zero failures, errors and manual
  checks. A `future_failure` count above 0 adds a warning to the run.
- **Leaves:** The `appinspect-report-<attempt>` artifact with HTML and JSON
  reports when produced, under **Artifacts** in the run.

## nonprod

- **When:** After `appinspect` succeeds on a pull request.
- **Needs:** The `dist` artifact, `splunk-appinspect` and
  `<target>-nonprod` variable groups, and the `<target>-nonprod` environment.
- **Does:** Installs the package on the configured stack through ACS.
- **Leaves:** No pipeline artifact. Deployment output is in the run logs.

## proddiff

- **When:** After the pull request's `nonprod` stage succeeds.
- **Needs:** The `dist` artifact and the `<target>-prod` variable group.
- **Does:** Exports the installed production app through the ACS CLI, then
  promotes local configuration into default files and compares only
  `default/` and `metadata/default.meta` with the package. If the app is not
  in production, the summary lists each package default file and
  `metadata/default.meta` as added.
- **Leaves:** The `prod-diff-<attempt>` artifact with `<app-id>.patch`,
  `<app-id>-summary.md`, and `<app-id>-merged.tar.gz`. Find it under
  **Artifacts** in the pull request run. The merged archive omits `local/`,
  `metadata/local.meta`, and `users/`.

## release

- **When:** After `appinspect` succeeds on a run whose source branch is `main`.
- **Needs:** The `dist` artifact and the app repo checkout.
- **Does:** Pushes the `v<version>` tag for the current commit and publishes
  the package as a Universal Package to `splunk-apps`.
- **Leaves:** No pipeline artifact. The Git tag is in Azure Repos. The package
  is in **Artifacts** under `splunk-apps`.

## prod

- **When:** After a successful `release`, when template parameter `prod` is
  `true`.
- **Needs:** The `dist` artifact, `splunk-appinspect` and `<target>-prod`
  variable groups, and the `<target>-prod` environment.
- **Does:** Installs the package on the configured production stack through
  ACS.
- **Leaves:** No pipeline artifact. Deployment output is in the run logs.
