"""Create an Azure Repos app repository from one Splunk app folder.

Usage:
    python new_app_repo.py <app-folder> --org https://dev.azure.com/<org>
        --project <project> --pool <agent-pool>

<app-folder> holds default/app.conf directly (no package folder). The script
creates a repository named after the folder, copies the folder into
package/, adds azure-pipelines.yml from example/, and pushes main.
Requires the Azure CLI with the azure-devops extension (az login first) and git.
Run once per app folder.
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

EXAMPLE = Path(__file__).parent / "example" / "azure-pipelines.yml"


def run(*cmd, cwd=None):
    print("##[command]" + " ".join(cmd), flush=True)
    # az is az.cmd on Windows; which() finds it.
    return subprocess.run([shutil.which(cmd[0]) or cmd[0], *cmd[1:]], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path)
    p.add_argument("--org", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--pool", required=True)
    a = p.parse_args()

    src = a.folder.resolve()
    if not (src / "default" / "app.conf").is_file():
        raise SystemExit(f"{src} has no default/app.conf")
    name = src.name

    url = run("az", "repos", "create", "--name", name, "--org", a.org, "--project", a.project,
              "--query", "remoteUrl", "-o", "tsv")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / name
        shutil.copytree(src, repo / "package", ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"))
        pipeline = EXAMPLE.read_text(encoding="utf-8").replace("<agent-pool>", a.pool)
        (repo / "azure-pipelines.yml").write_text(pipeline, encoding="utf-8")
        run("git", "init", "-b", "main", cwd=repo)
        run("git", "add", ".", cwd=repo)
        run("git", "commit", "-m", f"Add {name}", cwd=repo)
        run("git", "push", url, "main", cwd=repo)
    print(f"Created {url}")


if __name__ == "__main__":
    main()
