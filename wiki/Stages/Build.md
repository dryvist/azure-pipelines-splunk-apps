# Build stage

[Home](/Home) > [Stages](/Stages) > Build stage

[[_TOC_]]

## Stage `build`

- **Does:** Plans the run, sorts and packages the app, and bumps the version
  on a pull request when the target branch has not changed it.
- **Inputs:** App repo, tools repo, Python 3.13, build reason and branch
  variables, `slim`, `ksconf`, and Splunk SDK packages.
- **Outputs:** `dist` pipeline artifact containing the app package.

### Job `build` in the build stage

- **Does:** Runs on the selected `pool` and prepares the package for later
  stages.
- **Inputs:** App repo; tools repo; `Build.Reason`, `Build.SourceBranch`, and
  default `setup` or the app repo override.
- **Outputs:** `dist` artifact and, for a successful pull request bump, a
  commit pushed to the pull request source branch.

## Version bump rules

`release.py bump` changes versions only on pull request runs when the source
and target version rows match and the target branch has not changed the
version. `[major]` increments major and resets minor and patch. `[minor]`
increments minor and resets patch to zero. Otherwise, the patch number
increments. The bump updates `version` in `[launcher]` and `[id]`, regenerates
`app.manifest`, commits both files, and pushes the commit to the pull request
source branch.

Steps, in order:

- **Checkout app (`checkout: self`):** Gets the app repo at `app` and keeps
  credentials for the bump push. **Inputs:** App repo revision.
  **Outputs:** `$(Pipeline.Workspace)/app` checkout.
- **Checkout tools (`checkout: tools`, default `setup`):** Gets the shared
  scripts. **Inputs:** `tools` repository resource. **Outputs:**
  `$(Pipeline.Workspace)/tools` checkout.
- **UsePythonVersion@0 (default `setup`):** Selects Python 3.13.
  **Inputs:** `versionSpec: 3.13`. **Outputs:** Python on `PATH`.
- **Use UTF-8 for Python files and output (default `setup`):** Sets
  `PYTHONUTF8=1` for later steps.
- **Show stage plan:** Prints each stage and its run condition.
  **Inputs:** Build reason and source branch.
  **Outputs:** Stage plan in the job log.
- **Install diff dependencies:** Installs pinned `ksconf` and Splunk SDK
  packages through `templates/diff-tools.yml`. **Inputs:** Python package
  index. **Outputs:** Compare commands in the Python environment.
- **Install packaging toolkit:** The shared dependency template adds the
  packaging toolkit for build and import jobs. **Inputs:** Python package
  index. **Outputs:** `slim` in the Python environment.
- **Bump PR version and manifest:** On pull request runs, sorts config files,
  checks the target version, updates matching version fields and manifest,
  commits, then pushes to the source branch. After a push it sets
  `bump.bumped`, and Package app, Publish artifact, and every later stage
  skip in that run. The bump commit starts the next validation run.
  **Inputs:** App files, target and source refs, commit message, and
  repository credentials.
  **Outputs:** Updated source branch or a printed skip reason.
- **Package app:** Sorts config files, stages the app, and creates the
  package. `.meta` files list `[]` first, then stanzas without `/`, then
  stanzas with `/`, each group in name order. **Inputs:** `package/` and installed packaging tools.
  **Outputs:** Package under `dist/`.
- **Publish artifact (`publish: dist`):** Publishes the package directory.
  **Inputs:** `$(Pipeline.Workspace)/app/dist`. **Outputs:** `dist` pipeline
  artifact.

## Related

- [App pipeline](/Pipelines/App-pipeline)
- [Artifacts](/Reference/Artifacts)
- [Import from nonprod](/Pipelines/Nonprod-import)

---

[Next: AppInspect stage >](/Stages/AppInspect)
