# Restart pipeline

[Home](/Home) > [Pipelines](/Pipelines) > Restart pipeline

[[_TOC_]]

## Behavior

The manual restart pipeline selects `nonprod` or `prod` and group prefix
`splunk` or `splunk-itsi`. It checks status. When `messages.restartRequired`
is true, it restarts the current stack and polls until it is false. It then
checks status again.

The restart job uses `workspace: clean: all`, Python 3.13, the shared ACS CLI
template, and the selected variable group. ACS steps map `ACS_TOKEN` to
`STACK_TOKEN` and pass the optional `SPLUNK_SEARCH_HEAD` value.

![Restart pipeline flow.](../diagrams/restart-pipeline.png)

## Related

- [Deploy pipeline](/Pipelines/Deploy-pipeline)
- [Variable groups](/Reference/Variable-groups)

---

[< Previous: Compare pipeline](/Pipelines/Compare-pipeline) |
[Next: Smoke-test pipeline >](/Pipelines/Smoke-test-pipeline)
