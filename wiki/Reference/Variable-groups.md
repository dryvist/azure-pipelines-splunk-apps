# Variable groups

[Home](/Home) > [Reference](/Reference) > Variable groups

[[_TOC_]]

## App pipeline

- `splunk-appinspect`: AppInspect stage; also declared by the Nonprod job.
- `splunk-nonprod`: Nonprod deployment.
- `splunk-itsi-nonprod`: Import from the nonprod ITSI search head.
- `splunk-prod`: Proddiff comparison with the search head installs replace,
  and the Prod deployment.
- `splunk-itsi-prod`: Proddiff comparison with the prod ITSI search head.

## Manual pipelines

- Deploy declares `splunk-appinspect` and the selected
  `splunk-<environment>` group.
- Restart selects the prefix and environment group for stack and optional
  search-head settings.
- Compare with target `splunk` uses `splunk-nonprod` and `splunk-prod`.
- Compare with target `splunk-itsi` uses `splunk-itsi-nonprod` and
  `splunk-itsi-prod`.
- Smoke test uses `splunk-appinspect` for login and the selected target group
  for Nonprod and Prod access checks.

Compare and smoke test select the `splunk` or `splunk-itsi` prefix. Keep
`SPLUNK_USERNAME`, `SPLUNK_STACK`, and `SPLUNK_SEARCH_HEAD` unlocked when
scripts read them directly. Keep secret values such as `SPLUNK_PASSWORD`
locked and map them in YAML.

![Groups selected by pipeline and environment.](../diagrams/variable-group-use.png)

## Related

- [Compare pipeline](/Pipelines/Compare-pipeline)
- [Smoke-test pipeline](/Pipelines/Smoke-test-pipeline)

---

[< Previous: Code layout](/Reference/Code-layout) |
[Next: Artifacts and diff reports >](/Reference/Artifacts)
