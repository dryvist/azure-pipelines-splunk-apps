# Code layout

Use this table to find the main release command and module files.

| File | Contents |
| --- | --- |
| `release.py` | Command list and CLI dispatch. |
| `splunk_release/__init__.py` | Package marker. |
| `splunk_release/azure.py` | Pipeline plan, HTTP requests, and log helpers. |
| `splunk_release/version.py` | App identity, versions, manifests, and Git. |
| `splunk_release/import_app.py` | Environment export import and pull request. |
| `splunk_release/package.py` | Configuration sorting, staging, and packaging. |
| `splunk_release/appinspect.py` | AppInspect requests, polling, and reports. |
| `splunk_release/acs.py` | ACS CLI install, sessions, deployment, and export. |
| `splunk_release/compare.py` | Archive comparison and deployment reports. |
| `smoke-test/smoke_test.py` | AppInspect, read-only ACS, and Azure DevOps rights checks. |
| `templates/acs-cli.yml` | ACS CLI setup for a job. |
| `templates/acs-step.yml` | Python step with the shared ACS environment. |
| `templates/diff-tools.yml` | Package and diff dependency installation. |
| `templates/python.yml` | Python 3.13 selection. |
| `templates/deploy.yml` | Per-package deploy steps. |
| `templates/import-steps.yml` | Import compare and pull request steps. |
| `templates/splunk-app.yml` | Shared app pipeline stages. |
| `tests/` | Unit tests for release commands. |

The app id comes from `[id] name` in `package/default/app.conf`. If absent,
`release.py` uses `BUILD_REPOSITORY_NAME`, then the working directory name.
