"""Azure Pipelines commands and logging helpers."""

import os
import subprocess
import sys
import urllib.error
import urllib.request

def run(cmd, **kwargs):
    """Print a command, then run it."""
    print("##[command]" + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, **kwargs)


def report_command_error(error):
    """Print one Azure Pipelines error with the failed command and exit code."""
    print(f"##[error]{' '.join(map(str, error.cmd))} exited with code {error.returncode}")


def http(url, headers, data=None, timeout=900):
    req = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    print(f"##[command]{req.get_method()} {url}", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}\n{e.read().decode(errors='replace')}")


def plan():
    """Print which stages this run executes and the rule behind each."""
    reason = os.environ.get("BUILD_REASON", "")
    branch = os.environ.get("BUILD_SOURCEBRANCH", "")
    pull_request, main = reason == "PullRequest", branch == "refs/heads/main"
    compare = pull_request or main
    print("##[section]Stage plan")
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
    for line in patch.decode("utf-8", "replace").splitlines():
        color = None
        if line.startswith("@@"):
            color = colors["@"]
        elif line.startswith("+") and not line.startswith("+++"):
            color = colors["+"]
        elif line.startswith("-") and not line.startswith("---"):
            color = colors["-"]
        print(f"{color}{line}\033[0m" if color else line)
