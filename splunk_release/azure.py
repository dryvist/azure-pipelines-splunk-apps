"""Azure Pipelines commands and logging helpers."""

import os
import subprocess
import sys
import urllib.error
import urllib.request


def log(level, message="", flush=False):
    """Write an Azure Pipelines logging command, or plain text outside Azure Pipelines."""
    azure = "TF_BUILD" in os.environ
    if level == "endgroup":
        if azure:
            print("##[endgroup]", flush=flush)
        return
    if azure:
        print(f"##[{level}]{message}", flush=flush)
        return
    prefix = {"command": "COMMAND: ", "error": "ERROR: ", "warning": "WARNING: "}.get(level, "")
    print(f"{prefix}{message}", flush=flush)


def run(cmd, **kwargs):
    """Print a command, then run it."""
    log("command", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, **kwargs)


def report_command_error(error):
    """Print one Azure Pipelines error with the failed command and exit code."""
    detail = error.stderr or error.stdout
    if isinstance(detail, bytes):
        detail = detail.decode("utf-8", "replace")
    detail = " ".join(str(detail).split()) if detail else ""
    message = f"{' '.join(map(str, error.cmd))} exited with code {error.returncode}"
    log("error", f"{message}: {detail}" if detail else message)


def report_system_exit(error):
    """Print one error line for a failure raised with a message."""
    if isinstance(error.code, str):
        log("error", " ".join(error.code.splitlines()))
        raise SystemExit(1)


def http(url, headers, data=None, timeout=900):
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    log("command", f"{req.get_method()} {url}", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}")
    except urllib.error.URLError as e:
        sys.exit(f"HTTP request failed: {e.reason}")


def plan():
    """Print which stages this run executes and the rule behind each."""
    reason = os.environ.get("BUILD_REASON", "")
    branch = os.environ.get("BUILD_SOURCEBRANCH", "")
    pull_request, main = reason == "PullRequest", branch == "refs/heads/main"
    compare = pull_request or main
    log("section", "Stage plan")
    print(f"Build.Reason = {reason}")
    print(f"Build.SourceBranch = {branch}")
    for stage, runs, rule in (
        ("build", True, "every run"),
        ("appinspect", True, "after build, unless the build pushed a version bump"),
        ("nonprod", compare, "pull request or refs/heads/main"),
        ("proddiff", compare, "pull request or refs/heads/main"),
        ("release", main, "refs/heads/main, after proddiff"),
    ):
        print(f"{stage:<11} {'RUNS' if runs else 'SKIPPED':<8} runs when {rule}")

def appinspect_link():
    """Print the link to this build's published artifacts."""
    print(
        f"{os.environ['SYSTEM_COLLECTIONURI']}{os.environ['SYSTEM_TEAMPROJECTID']}/_build/results"
        f"?buildId={os.environ['BUILD_BUILDID']}&view=artifacts&pathAsName=false&type=publishedArtifacts"
    )

def print_colored_patch(patch):
    colors = {"+": "\033[32m", "-": "\033[31m", "@": "\033[36m"}
    text = patch.decode("utf-8", "replace") if isinstance(patch, bytes) else str(patch)
    use_color = "TF_BUILD" in os.environ or sys.stdout.isatty()
    for line in text.splitlines():
        color = None
        if line.startswith("@@"):
            color = colors["@"]
        elif line.startswith("+") and not line.startswith("+++"):
            color = colors["+"]
        elif line.startswith("-") and not line.startswith("---"):
            color = colors["-"]
        elif "[added]" in line.lower() or line.startswith(("PASS ", "NO DIFFERENCES", "RESULT: ALL PASS")):
            color = colors["+"]
        elif "[removed]" in line.lower() or line.startswith(("FAIL ", "RESULT: FAILED")):
            color = colors["-"]
        elif "[changed]" in line.lower():
            color = "\033[33m"
        print(f"{color}{line}\033[0m" if use_color and color else line)
