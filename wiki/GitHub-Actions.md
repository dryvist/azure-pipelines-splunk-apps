# GitHub Actions outlook

This page compares the Azure Pipelines concepts in this wiki with GitHub Actions. The pipelines in this repository
run on Azure Pipelines. This page is forward-looking only.

| Azure DevOps concept | GitHub Actions equivalent | Notes |
| --- | --- | --- |
| Pipeline YAML | A workflow file under `.github/workflows/` | One workflow file for each pipeline. |
| Templates | Reusable workflows (job-level `uses`) or composite actions | Reusable workflows fit stage templates. Composite actions fit step lists. |
| Runtime parameters | `workflow_dispatch` inputs | Limit: 25 top-level inputs, and 65,535 characters for the inputs payload. |
| Variable groups | Environment or repository secrets, and variables | Secrets are documented at repository and environment level. |
| Environments, approvals, and timeout | Environments with required reviewers and a wait timer | No confirmed GitHub equivalent for the approval Timeout. |
| `System.AccessToken` | `GITHUB_TOKEN`, created for each job | For pull requests a workflow creates, use a GitHub App installation token instead. |
| Azure Artifacts feed of Universal Packages | GitHub release assets | No confirmed GitHub equivalent for Universal Packages. |
| Build validation policy | Ruleset required status checks | Set on the protected branch. |
| Schedules | `on: schedule` | Cron expressions, in UTC by default. |
| `##vso` logging commands | Workflow commands such as `::error` and `::warning`, and the job summary (`GITHUB_STEP_SUMMARY`) | |
| Onboard REST calls | Create the repository from a template repository | |

What stays the same:

- The `release.py` commands and the ACS CLI calls run unchanged inside a job step.
- Splunk stack and app variable names keep their names.
- Approval before a prod install, and the one-at-a-time lock, still apply.
- The package names, the AppInspect step, and the compare reports keep their formats.
