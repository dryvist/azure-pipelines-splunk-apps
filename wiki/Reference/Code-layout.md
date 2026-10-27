# Code layout

Use this table to find the main release command, the module files, and the templates.

| File | Contents |
| --- | --- |
| `release.py` | Command list and CLI dispatch. |
| `splunk_release/__init__.py` | Package marker. |
| `splunk_release/azure.py` | Pipeline plan, HTTP requests, and log helpers. |
| `splunk_release/version.py` | App identity, versions, manifests, and Git. |
| `splunk_release/import_app.py` | Environment export import, onboarding, and pull request. |
| `splunk_release/package.py` | Configuration sorting, staging, and packaging. |
| `splunk_release/appinspect.py` | AppInspect requests, polling, and reports. |
| `splunk_release/acs.py` | ACS CLI install, sessions, deployment, waits, and export. |
| `splunk_release/compare.py` | Archive comparison and deployment reports. |
| `smoke-test/smoke_test.py` | AppInspect, read-only ACS, and Azure DevOps rights checks. |
| `templates/splunk-app.yml` | Shared app pipeline stages, extended by each app repository. |
| `templates/acs-bulk-stage.yml` | One bulk install, update, or delete stage, and its restart stage when selected. |
| `templates/acs-cli.yml` | ACS CLI setup for a job. |
| `templates/acs-step.yml` | Python step with the shared ACS environment. |
| `templates/compare-stage.yml` | One stage that compares a package with an environment's search head and its ITSI search head. |
| `templates/compare-steps.yml` | Shared app comparison steps. |
| `templates/deploy-stage.yml` | One stage that installs, or with uninstall removes, a package on an environment. |
| `templates/deploy.yml` | Shared per-package steps for app validation and deployment. |
| `templates/diff-tools.yml` | Dependency installation for package and diff commands. |
| `templates/dist-package.yml` | App pipeline setup steps, then download of the run's package artifact. |
| `templates/feed-package.yml` | Checks out the tools repository, then downloads one app package from the splunk-apps feed. |
| `templates/import-steps.yml` | Compares an environment's installed app with the `main` package, then opens a pull request. |
| `templates/python.yml` | Python 3.13 selection. |
| `templates/restart-stage.yml` | One stage that restarts the ITSI search head, then the main search head, when ACS reports a restart. |
| `tests/` | Unit tests for release commands. |

The app ID comes from `[id] name` in `package/default/app.conf`. If it is absent, `release.py` uses
`BUILD_REPOSITORY_NAME`, then the working directory name.
