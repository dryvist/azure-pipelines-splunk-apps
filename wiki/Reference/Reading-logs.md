# Reading logs

Use this page to identify commands, warnings, and failures in a pipeline log.

- `##[command]` lines show commands run by the script.
- Each comparison app has one section naming the target and source.
- `##[warning]` lines identify non-failing notices such as `future_failure`.
- `##[error]` lines report failures without a traceback.
- Azure Pipelines logging prefixes appear only when `TF_BUILD` is set. Outside
  the pipeline, errors and warnings use `ERROR:` and `WARNING:` prefixes.
- Result lines use color in Azure Pipelines or when output is a terminal.
- The AppInspect JSON appears in the report step; its HTML link points to the
  artifact for that run.
- Disable **Enable system diagnostics** on the Run panel when its output is
  not needed.

See [Artifacts](/Reference/Artifacts) for artifact names and contents.
