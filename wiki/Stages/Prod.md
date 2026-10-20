# Prod stage

[Home](/Home) > [Stages](/Stages) > Prod stage

[[_TOC_]]

## Stage `prod`

- **Display name:** `Deploy to prod`.
- **Does:** Runs after Release on successful `refs/heads/main` runs.
- **Inputs:** `dist`, groups `splunk-appinspect` and `splunk-prod`, and the
  `splunk-prod` environment.
- **Outputs:** `prod-diff-<app>-<attempt>` artifact and app installation
  through ACS.
- **Approval:** Waits for the `splunk-prod` Approvals check. Nothing installs
  without approval. A rejection stops the stage. If approval reaches its
  Timeout, Azure marks the stage skipped.
- **Lock:** Uses sequential lock behavior. The Exclusive Lock check runs after
  approvals, so waiting for approval does not hold the prod lock.

### Deployment job `deploy`

- **Display name:** `Compare with prod and install`.
- **Does:** Compares the package with prod, then installs it through ACS.
- **Inputs:** `dist`, `splunk-prod`, Python setup, `SPLUNK_STACK`, and
  `ACS_TOKEN`.
- **Outputs:** Production compare report and installed app.

## Related

- [Release stage](/Stages/Release)
- [Nonprod stage](/Stages/Nonprod)
- [Deploy to production](/Pipelines/Deploy-to-production)

---

[< Previous: Release stage](/Stages/Release)
