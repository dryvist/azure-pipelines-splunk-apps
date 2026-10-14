# Troubleshooting

[[_TOC_]]

Follow the pipeline from the first failed step. A skipped stage can be the
result of an earlier job or a run condition.

## Before the first stage

### Variable group not found or not authorized

**Symptom:** `Variable group  was not found`, a named group was not found, or
the run says **This pipeline needs permission**.

**Cause:** Group names must match the pipeline reference exactly. These
pipelines use hyphens, such as `splunk-appinspect`, not underscores. The
pipeline may also lack permission to use a group or environment.

**Fix:**

1. Compare each requested group name with the names in
   **Pipelines → Library**.
2. Rename any group that uses underscores to the exact hyphenated name.
3. Select **View** in the permission banner.
4. Select **Permit** for each requested variable group.
5. Select **Permit** for each requested deployment environment.
6. If no banner appears, add the pipeline under each group's **Pipeline
   permissions**.
7. If no banner appears, add the pipeline under each environment's
   **Security → Pipeline permissions**.

**Docs:** [Variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups),
[environments](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/environments),
[approvals](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/approvals).

### `A template expression is not allowed in this context` for `pool`

**Symptom:** Pipeline validation rejects the `pool` template expression.

**Cause:** The shared template sets `pool` from its `pool` parameter. A pool
must also be selected in the pipeline settings for pipelines that do not
extend that template.

**Fix:**

1. Open the pipeline and select **Edit**.
2. Select **… → Triggers → YAML**.
3. Set **Default agent pool for YAML**.
4. In an app repo, set the `pool` value under the template's `parameters`.

**Docs:** [Runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters),
[expressions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

### Agent setup and network access

#### Python 3.13 is not available on a self-hosted agent

**Symptom:** `UsePythonVersion@0` cannot find Python 3.13.

**Cause:** The task finds Python versions in the agent tool cache. The required
version is not in `_work/_tool/Python/3.13.x/x64`.

**Fix:**

1. Install Python 3.13 x64 in `_work/_tool/Python/3.13.x/x64` on the agent.
2. Rerun the failed job.

**Docs:** [Use Python version](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

#### `Unable to locate executable file: 'bash'`

**Symptom:** The job reports `Unable to locate executable file: 'bash'` on a
Windows agent.

**Cause:** The selected agent does not provide the shell expected by the
pipeline task. The YAML uses one command per `script` step. Most commands call
Python; the ACS version step calls `acs version` directly.

**Fix:**

1. Select a Linux agent pool for this pipeline.
2. For compare and smoke-test pipelines, set **Default agent pool for YAML**
   under **Edit → … → Triggers → YAML**.
3. For an app pipeline, set it in the app repo's `pool` template parameter.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters).

#### `CERTIFICATE_VERIFY_FAILED ... unable to get local issuer certificate`

**Symptom:** The ACS CLI download fails certificate verification in `curl`.

**Cause:** HTTPS inspection presents a certificate issuer the agent does not
trust. `curl` uses the operating system certificate store.

**Fix:**

1. Add the HTTPS inspection root certificate to the agent OS trust store.
2. Rerun **Install ACS CLI 2.26.0**.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

#### Agent cannot reach a required service

**Symptom:** A download, package install, login, or API request times out or
cannot resolve its service.

**Cause:** The agent cannot make outbound HTTPS requests to a required host.

**Fix:**

1. Allow agent outbound HTTPS to `github.com` for the ACS CLI download.
2. Allow agent outbound HTTPS to `pypi.org` for Python packages.
3. Allow agent outbound HTTPS to `api.splunk.com` for AppInspect login.
4. Allow agent outbound HTTPS to `appinspect.splunk.com` for validation.
5. Allow agent outbound HTTPS to `admin.splunk.com` for ACS requests.
6. Rerun the failed job.

**Docs:** [Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents),
[AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[ACS CLI](https://github.com/splunk/acs-cli).

## Build stage

::: mermaid
flowchart LR
    Build[Stage: build] --> Plan([Step: Show stage plan])
    Plan --> Bump([Step: Bump PR version and manifest])
    Bump --> Package([Step: Package app])
    Package --> Dist[(Artifact: dist package)]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Build stage
    class Plan,Bump,Package step
    class Dist step
:::

### A stage after AppInspect is skipped

**Symptom:** `nonprod`, `proddiff`, `release`, or `prod` is marked skipped.

**Cause:** `Show stage plan` prints the run reason, branch, `prod` parameter,
and the condition for each stage. `nonprod` requires a pull request. `proddiff`
depends on `nonprod`. `release` requires `refs/heads/main`. `prod` requires a
successful release and `prod: true` in the app repo template parameters.

**Fix:**

1. Open the build job and read **Show stage plan**.
2. For `nonprod` and `proddiff`, run validation for a pull request.
3. Add a Build Validation branch policy on the pull request target branch.
4. For `release`, run a build from `main` so the source ref is
   `refs/heads/main`.
5. For `prod`, set `prod: true` in the app repo's template parameters.

**Docs:** [Conditions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions),
[expressions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions),
[branch policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies).

### Bump step prints a skip reason

**Symptom:** The step can print `target app.conf is missing, skipping bump`
or `version already changed, skipping bump`. `release.py` also has the
message `not a PR validation build, skipping bump`, but the pipeline condition
skips the step before it runs outside a pull request.

**Cause:** The bump runs only for a pull request. It also skips when the target
branch has no app config or already has a different version.

**Fix:**

1. Run pull request validation when a version bump is needed.
2. Add `package/default/app.conf` to the app repo if it is missing.
3. If the target version already changed, review that version before merging.

**Docs:** [Conditions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions),
[Git commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/git-commands).

### Bump push is rejected

**Symptom:** `Bump PR version and manifest` fails while pushing to the source
branch.

**Cause:** The project Build Service identity cannot contribute to the app
repository.

**Fix:**

1. Allow **Contribute** for the project Build Service identity on the app repo.
2. Rerun pull request validation.

**Docs:** [Git commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/git-commands),
[branch policies](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies).

### Version mismatch in `app.conf`

**Symptom:** The log says that `[launcher]` and `[id]` need the same
`version` in `package/default/app.conf`.

**Cause:** The `[launcher]` and `[id]` version values differ or one is missing.

**Fix:**

1. Set the same version in `[launcher]` and `[id]` in
   `package/default/app.conf`.
2. Rerun the build.

**Docs:** [Packaging toolkit](https://dev.splunk.com/enterprise/docs/releaseapps/packagingtoolkit/).

### `ksconf sort` moves comments

**Symptom:** Comments move when the build sorts `.conf` files.

**Cause:** `ksconf sort` sorts configuration stanzas and keys.

**Fix:**

1. Add `KSCONF-NO-SORT` to the file comment to opt that file out of sorting.

**Docs:** [ksconf sort](https://ksconf.readthedocs.io/en/stable/cmd_sort.html).

### `Artifact ... already exists` on a rerun

**Symptom:** Publish reports that an artifact with the same name already
exists.

**Cause:** Names differ by output. The shared template uses the job attempt
for `appinspect-report` and the `*-diff` artifacts. The build `dist` artifact
and the compare pipeline's `nonprod-export`, `prod-export`, and `compare`
artifacts have fixed names.

**Fix:**

1. For a fixed-name artifact collision, start a new pipeline run.
2. For an attempt-named report or diff, open the artifact with the matching
   `System.JobAttempt` suffix.

**Docs:** [Pipeline artifacts](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts).

## AppInspect stage

::: mermaid
flowchart LR
    Inspect[Stage: appinspect] --> Dist[(Artifact: dist package)]
    Dist --> Run([Step: Run AppInspect])
    Run --> Reports[(Artifact: appinspect report for this attempt)]
    Run --> Result([Step: show JSON and HTML report link])
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Inspect stage
    class Run,Result step
    class Dist,Reports step
:::

### `KeyError: 'SPLUNK_USERNAME'`

**Symptom:** `Run AppInspect` exits with `KeyError: 'SPLUNK_USERNAME'`.

**Cause:** Locked variables reach scripts only when mapped. The AppInspect
step maps the password, but reads the unlocked username variable directly.

**Fix:**

1. Keep `SPLUNK_USERNAME` unlocked in `splunk-appinspect`.
2. Keep `SPLUNK_STACK` unlocked in each stack group.
3. Keep `SPLUNK_SEARCH_HEAD` unlocked in each ITSI group.
4. Keep secret values such as `SPLUNK_PASSWORD` locked and mapped in YAML.

**Docs:** [Secret variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables),
[variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups).

### `ValueError: too many values to unpack (expected 1)`

**Symptom:** `Run AppInspect` or a deploy step stops at
`(pkg,) = Path(artifact_dir).glob("*.tar.gz")`.

**Cause:** The `dist` folder holds more than one package. Self-hosted agents
keep files between runs unless the job cleans its workspace.

**Fix:**

1. Open `templates/splunk-app.yml` in `azure-pipelines-splunk-apps`.
2. Check that every job has `workspace:` with `clean: all`.
3. Run the pipeline again.

**Docs:**
[Pipeline artifacts](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts),
[Agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents)

### AppInspect login returns 401 or 403

**Symptom:** The log shows `HTTP 401` or `HTTP 403` from the AppInspect login
request to `api.splunk.com`.

**Cause:** The AppInspect username or password is incorrect, missing, or not
available to the script.

**Fix:**

1. Set `SPLUNK_USERNAME` to the account username in `splunk-appinspect`.
2. Set `SPLUNK_PASSWORD` to that account's password.
3. Keep the username unlocked and map the locked password to the script.
4. Rerun the `appinspect` job.

**Docs:** [AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[secret variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/set-secret-variables).

### AppInspect does not pass

**Symptom:** The log prints `AppInspect did not pass` or a summary with
failures, errors, or manual checks.

**Cause:** The stage passes only when status is `SUCCESS` and the failure,
error, and manual check counts are all zero. A `future_failure` count adds a
warning, but does not fail this check.

**Fix:**

1. Open **Show AppInspect JSON report** in the failed job.
2. Open the link from **Show AppInspect HTML report link**.
3. Open `appinspect-report-<attempt>` for the failed job attempt.
4. Fix each reported failure, error, or manual check in the app.
5. Rerun validation after fixing the findings.

**Docs:** [AppInspect](https://dev.splunk.com/enterprise/docs/developapps/testvalidate/appinspect/),
[pipeline artifacts](https://learn.microsoft.com/en-us/azure/devops/pipelines/artifacts/pipeline-artifacts).

## Nonprod stage

::: mermaid
flowchart LR
    Nonprod[Stage: nonprod] --> Export([Step: export target app])
    Export --> Diff[(Artifact: nonprod diff for this attempt)]
    Diff --> Deploy([Step: install package through ACS])
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Nonprod stage
    class Export step
    class Diff step
    class Deploy deploy
:::

### ACS token is rejected or lacks access

**Symptom:** An ACS command returns HTTP 401 or 403 during login, export, or
install.

**Cause:** `SPLUNK_STACK` may name the wrong target. The token may have the
wrong audience, may be from a different stack or search head, or lack an ACS
capability.

**Fix:**

1. Set `SPLUNK_STACK` to the stack name used in its service URL.
2. Create the token on that stack or its selected search head.
3. Set the token audience to `acs`.
4. Grant the account `export_apps`, `install_apps`, and `edit_local_apps`.
5. Put the token in `ACS_TOKEN` in the matching variable group.
6. Rerun the failed job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[ACS CLI](https://github.com/splunk/acs-cli).

### Agent address is missing from the ACS allowlist

**Symptom:** ACS requests from an agent fail even though stack and token
settings are correct.

**Cause:** The agent's outbound address is not allowed for one or both ACS
features used by the pipeline.

**Fix:**

1. Add the agents' outbound addresses to the `acs` feature allowlist.
2. Add the agents' outbound addresses to the `search-api` feature allowlist.
3. Rerun the failed job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/agents).

## Proddiff stage

::: mermaid
flowchart LR
    Proddiff[Stage: proddiff] --> Export([Step: export production app])
    Export --> Compare([Step: compare production with package])
    Compare --> Reports[(Artifact: prod diff for this attempt)]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Proddiff stage
    class Export,Compare step
    class Reports step
:::

### Diff output is missing or unexpected

**Symptom:** The `prod-diff-<attempt>` artifact is missing, or the summary
shows added, changed, or removed defaults.

**Cause:** The export or diff command failed, or production differs from the
package. Local files are compared with matching package defaults before the
script promotes local files, sorts defaults, and compares deployed defaults.

**Fix:**

1. Read the first failed export or diff step in the `proddiff` job.
2. Open the `prod-diff-<attempt>` artifact for that job attempt.
3. Review the local-versus-default report, patch, and summary.
4. Update the app package or resolve the production difference before merge.

**Docs:** [ksconf filter](https://ksconf.readthedocs.io/en/stable/cmd_filter.html),
[ksconf diff](https://ksconf.readthedocs.io/en/stable/cmd_diff.html),
[ksconf promote](https://ksconf.readthedocs.io/en/stable/cmd_promote.html),
[ksconf sort](https://ksconf.readthedocs.io/en/stable/cmd_sort.html).

## Release stage

::: mermaid
flowchart LR
    Release[Stage: release] --> Tag([Step: tag release version])
    Tag --> Feed([Step: publish package])
    Feed --> Package[(Artifact feed: versioned package)]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Release stage
    class Tag,Feed step
    class Package step
:::

### Tag push is rejected

**Symptom:** The tag step cannot push `v<version>` because the tag exists on
another commit.

**Cause:** A tag name already points to a different commit in the remote repo.

**Fix:**

1. Set a new unused version in both `[launcher]` and `[id]` in `app.conf`.
2. Merge the version change to `main`.
3. Rerun the release pipeline.

**Docs:** [Git commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/git-commands),
[packaging toolkit](https://dev.splunk.com/enterprise/docs/releaseapps/packagingtoolkit/).

### Feed publish fails because the version exists

**Symptom:** Universal Package publish reports that the package version
already exists.

**Cause:** The feed already contains that app id and version.

**Fix:**

1. Set a new unused version in both `[launcher]` and `[id]` in `app.conf`.
2. Merge the version change to `main`.
3. Rerun the release pipeline.

**Docs:** [Universal Packages](https://learn.microsoft.com/en-us/azure/devops/artifacts/quickstarts/universal-packages),
[packaging toolkit](https://dev.splunk.com/enterprise/docs/releaseapps/packagingtoolkit/).

## Prod stage

::: mermaid
flowchart LR
    Prod[Stage: prod] --> Export([Step: export production app])
    Export --> Diff[(Artifact: prod diff for this attempt)]
    Diff --> Deploy([Step: install package through ACS])
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Prod stage
    class Export step
    class Diff step
    class Deploy deploy
:::

### Production deployment does not start

**Symptom:** The `prod` stage is absent or skipped.

**Cause:** The template adds it only when `prod: true`; it also depends on a
successful `release` stage from `refs/heads/main`.

**Fix:**

1. Set `prod: true` in the app repo template parameters.
2. Run the pipeline from `main`.
3. Read **Show stage plan** in the build job.

**Docs:** [Conditions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions),
[runtime parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/runtime-parameters).

## Compare pipeline

The compare pipeline exports each selected app from nonprod and prod, then
compares prod as the target with nonprod as the source.

::: mermaid
flowchart LR
    Nonprod([Job: export nonprod]) --> NonprodFiles[(Artifact: nonprod-export)]
    Prod([Job: export prod]) --> ProdFiles[(Artifact: prod-export)]
    NonprodFiles --> Compare([Job: compare prod with nonprod])
    ProdFiles --> Compare
    Compare --> Reports[(Artifact: compare)]
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class Nonprod,Prod,Compare step
    class NonprodFiles,ProdFiles,Reports step
:::

### Search head is empty or not configured

**Symptom:** The smoke-test job prints `FAIL <group>: empty value for
SPLUNK_SEARCH_HEAD`, or ACS reports that the search head is not configured or
not added.

**Cause:** The selected ITSI variable group lacks the exact
`SPLUNK_SEARCH_HEAD` name or value. Azure then passes the literal
`$(SPLUNK_SEARCH_HEAD)`. The script sets the target with
`acs config add-stack --target-sh`.

**Fix:**

1. Set the exact variable name `SPLUNK_SEARCH_HEAD` in the selected ITSI group.
2. Set it to the search head name for the same stack as `SPLUNK_STACK`.
3. Create the ACS token on that search head with audience `acs`.
4. Keep `SPLUNK_SEARCH_HEAD` unlocked in the variable group.
5. Rerun the failed job.

**Docs:** [ACS CLI](https://github.com/splunk/acs-cli),
[ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[variable groups](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/variable-groups).

## Smoke-test pipeline

::: mermaid
flowchart LR
    AppInspect([Job: check login]) --> Result([Job: report results])
    Nonprod([Job: check nonprod ACS and export]) --> Result
    Prod([Job: check prod ACS and export]) --> Result
    classDef step fill:#FFFFFF,stroke:#CBD5E1,color:#101828,stroke-width:1px
    classDef stage fill:#EFF6FF,stroke:#0054A3,color:#101828,stroke-width:2px
    classDef deploy fill:#0054A3,stroke:#0054A3,color:#FFFFFF,stroke-width:2px
    classDef risk fill:#FFF7ED,stroke:#B54708,color:#101828,stroke-width:2px
    classDef skip fill:#F1F5F9,stroke:#CBD5E1,color:#475467,stroke-dasharray:4 3
    linkStyle default stroke:#475467
    class AppInspect,Nonprod,Prod,Result step
:::

### ACS reports `WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED`

**Symptom:** ACS returns HTTP 400 with
`WITH SEARCH APPS ONLY LOCAL AND USERS CONFIGS ALLOWED` while exporting the
built-in `search` app.

**Cause:** The built-in search app allows local and user configuration files
only. The smoke-test export is limited to those files. The compare pipeline
exports full app content, so do not include the built-in `search` app there.

**Fix:**

1. Keep the smoke-test export at `--default=false`.
2. Keep `--local=true` and `--users=true` for the smoke-test export.
3. Keep `--confs-only=true` for the smoke-test export.
4. Remove `search` from the compare pipeline app id list.
5. Rerun the affected job.

**Docs:** [ACS export apps](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/10.5.2605/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/export-apps-in-splunk-cloud-platform),
[ACS CLI](https://github.com/splunk/acs-cli).

### Read the smoke-test result

**Symptom:** The `result` job prints `RESULT: FAILED`.

**Cause:** At least one of `appinspect`, `nonprod`, or `prod` did not finish
with `Succeeded`.

**Fix:**

1. Open each failed job named in the `Result` step output.
2. Read its first `FAIL` or `Error` line.
3. Fix that job's credential, network, or export issue.
4. Rerun the smoke-test pipeline.

**Docs:** [Conditions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/conditions),
[logging commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands).

## Read the run log

### System diagnostics add too much output

**Symptom:** The run log contains large amounts of system diagnostic output.

**Cause:** **Enable system diagnostics** was selected on the Run panel.

**Fix:**

1. Untick **Enable system diagnostics** on the Run panel before starting the
   next run.

**Docs:** [Logging commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands).

### Identify commands, sections, and warnings

**Symptom:** The job log is hard to scan.

**Cause:** Commands and messages are mixed into the action log.

**Fix:**

1. Read blue `##[command]` lines as commands run by the script.
2. Use green section headings to find the start of an action.
3. Read yellow warning lines for non-failing notices such as `future_failure`.

**Docs:** [Logging commands](https://learn.microsoft.com/en-us/azure/devops/pipelines/scripts/logging-commands).
