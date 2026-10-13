# Troubleshooting

[[_TOC_]]

| Symptom | Fix |
| --- | --- |
| Version mismatch | Match `[id]` and `[launcher]` in `app.conf`. |
| Bump skipped | Check target `app.conf` and the pull request version. |
| Bump push fails | Grant Build Service `Contribute` on the source branch. |
| Tag push fails | Grant Build Service `Create tag` on the app repo. |
| Feed publish fails | Grant `Feed Publisher (Contributor)` on `splunk-apps`. |
| Feed version exists | Release a new version; feed versions cannot repeat. |
| AppInspect fails | Check credentials and `appinspect-report-<attempt>`. |
| ACS 401 or 403 | Check `ACS_TOKEN`; production export needs `export_apps`. |
| ACS 404 | Check that `SPLUNK_STACK` names the intended stack. |
| `proddiff` missing | Check PR AppInspect/nonprod success and run artifacts. |
| Production stage missing | Check `main`, release success, and `prod: true`. |
| Resource access fails | Authorize the repo, groups, environment, or feed. |
