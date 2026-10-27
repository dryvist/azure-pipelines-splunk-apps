# Setup

One time. Done at project setup; you should not need this again.

Prepare a project once. Work through the pages in the order below.

## Before you start

- Project Administrator access to an Azure DevOps project in `<org>`.
- The `azure-pipelines-splunk-apps` repository in that project's Azure Repos.
- A Splunk account for AppInspect, with its username and password.
- The nonprod and prod Splunk Cloud stack names.
- The ITSI search head names from the provisioning information for both stacks.
- Access to create ACS tokens on both stacks and their ITSI search heads. The required account capabilities are
  in [Environments and ACS](/Setup/Environments-and-ACS).
- Azure agents with Python 3.13 and outbound network access. See [Agent](/Setup/Agent).
- Apps installed this way are private apps. A copy of a Splunkbase app needs its own app ID in `[id] name`,
  different from the Splunkbase app ID.

Select the target project, `<project>`, in the Azure DevOps organization, `<org>`.

## Order

1. [Package feed](/Setup/Feed)
2. [Variable groups](/Setup/Variable-groups)
3. [Environments and ACS](/Setup/Environments-and-ACS)
4. [Agent](/Setup/Agent)
5. [Build Service](/Setup/Build-service)
6. [Manual pipelines](/Setup/Manual-pipelines)
7. [Publish the wiki](/Setup/Publish-wiki)

For each app, use [Onboard](/Pipelines/Onboard). Use the [manual app appendix](/Setup/Appendix-manual-app) only
if Onboard cannot run.
