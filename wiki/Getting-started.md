# Getting started

[Home](/Home) > Getting started

[[_TOC_]]

Use this checklist to open each setup procedure.

| Step | Purpose |
| --- | --- |
| [Step 1](/Getting-started/Feed) | Create the package feed and grant publish access. |
| [Step 2](/Getting-started/Variable-groups) | Create the five variable groups. |
| [Step 3](/Getting-started/Environments-and-ACS) | Create the two deployment environments. |
| [Step 4](/Getting-started/Environments-and-ACS) | Create ACS tokens and grant export access. |
| [Step 5](/Getting-started/App-repository) | Create an app repository and add its pipeline files. |
| [Step 6](/Getting-started/App-repository) | Grant the Build Service app repository permissions. |
| [Step 7](/Getting-started/App-pipeline) | Create a pipeline from the existing YAML file. |
| [Step 8](/Getting-started/App-pipeline) | Permit the pipeline to use its resources. |
| [Step 9](/Getting-started/App-pipeline) | Require pipeline validation for pull requests to `main`. |
| [Step 10](/Getting-started/App-pipeline) | Check the first pull request run and its artifacts. |
| [Step 11](/Getting-started/Release) | Check the first release after merging. |
| [Step 12](/Getting-started/Manual-deploy) | Create the manual app deployment pipeline. |
| [Step 13](/Getting-started/Publish-wiki) | Publish the repository wiki. |
| [Step 14](/Getting-started/Compare) | Create the environment compare pipeline. |
| [Step 15](/Getting-started/Restart) | Create the stack restart pipeline. |
| [Step 16](/Getting-started/Bulk-pipelines) | Create the ACS bulk install pipeline. |
| [Step 17](/Getting-started/Bulk-pipelines) | Create the ACS bulk update pipeline. |
| [Step 18](/Getting-started/Bulk-pipelines) | Create the ACS bulk delete pipeline. |
| [Step 19](/Getting-started/Repair) | Allow the agent on the search head REST API. |
| [Step 20](/Getting-started/Repair) | Add the REST URL for search head groups. |
| [Step 21](/Getting-started/Repair) | Create the app object repair pipeline. |

## Before you start

- Project Administrator access to an Azure DevOps project in `<org>`.
- The `azure-pipelines-splunk-apps` repository in that project's Azure
  Repos.
- A Splunk account for AppInspect, with its username and password.
- The nonprod and prod Splunk Cloud stack names.
- The ITSI search head names from the provisioning information for both stacks.
- Access to create ACS tokens on both stacks and their ITSI search heads.
  Each token account needs `export_apps`. Standard stack deploy tokens also
  need `install_apps` and `edit_local_apps`.
- Azure agents must have Python 3.13 available in the UsePythonVersion tool
  cache.
- Apps installed this way are private apps. A copy of a Splunkbase app needs
  its own app id in `[id] name`, different from the Splunkbase app id.
- Outbound HTTPS from Azure Pipelines agents to `pypi.org`, `api.splunk.com`,
  `appinspect.splunk.com`, `admin.splunk.com`, and `github.com`. Pipelines
  download the ACS CLI from `github.com`.

Select the target project, `<project>`, in the Azure DevOps organization,
`<org>`.

## If a step fails

| Symptom | Fix |
| --- | --- |
| ACS returns 401 or 403 | Check stack, token, `acs` audience, capabilities. |
| `NOT INSTALLED <app-id>` | Expected for a new app; files show as added. |
| Push denied | Allow Build Service **Contribute** and **Create tag**. |
| AppInspect fails | Check `appinspect-report-<attempt>` and fix its findings. |
| Permission prompt | Select **Permit** for the repo, groups, environments. |

## Related

- [Home](/Home)

---

[< Previous: Home](/Home) |
[Next: Pipelines >](/Pipelines)
