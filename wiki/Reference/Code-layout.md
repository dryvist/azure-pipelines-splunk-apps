# Code layout

[Home](/Home) > [Reference](/Reference) > Code layout

[[_TOC_]]

| File | Contents |
| --- | --- |
| `release.py` | Command list and CLI dispatch. |
| `splunk_release/__init__.py` | Package marker. |
| `splunk_release/azure.py` | Pipeline plan, artifact link, and log helpers. |
| `splunk_release/version.py` | App id, version changes, and Git operations. |
| `splunk_release/package.py` | Configuration sorting, staging, and packaging. |
| `splunk_release/appinspect.py` | AppInspect requests, polling, and reports. |
| `splunk_release/acs.py` | ACS CLI install, sessions, deployment, and export. |
| `splunk_release/compare.py` | Archive comparison and deployment reports. |

The app id comes from `[id] name` in `package/default/app.conf`. If absent,
`release.py` uses `BUILD_REPOSITORY_NAME`, then the working directory name.

## Related

- [release.py commands](/Reference/Release.py-commands)

---

[< Previous: release.py commands](/Reference/Release.py-commands) |
[Next: Variable groups >](/Reference/Variable-groups)
