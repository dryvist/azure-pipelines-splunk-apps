# Reading the run log

Use this page to cut diagnostic noise from a run log, and to find commands, sections, warnings, and failures.

## System diagnostics add too much output

**Symptom:** The run log contains large amounts of system diagnostic output.

**Fix:** Clear **Enable system diagnostics** on the Run panel before the next run.

## Find commands, sections, and warnings

- `##[command]` lines show the commands that a script runs.
- Each comparison app has one section that names the target and the source.
- `##[warning]` lines are notices that do not fail the run, such as `future_failure`.
- `##[error]` lines report failures without a traceback.
- Azure Pipelines logging prefixes appear only when `TF_BUILD` is set. Outside the pipeline, errors and
  warnings use `ERROR:` and `WARNING:` prefixes.
- Result lines use color in Azure Pipelines, or when the output is a terminal.
- The AppInspect JSON appears in the report step. Its HTML link points to the artifact for that run.

For artifact names and contents, see [Artifacts](/Reference/Artifacts).
