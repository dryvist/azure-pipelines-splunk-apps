# Edit files in VS Code

Use VS Code to clone the repository, edit folders, and commit from a local copy. The browser steps are in
[Edit files in the browser](/Editing/Browser).

## One time

One time, per workstation. Do these steps once.

1. Install **Git for Windows** from git-scm.com. In the installer, set the default branch name to `main`.
   Use the bundled OpenSSH. Include **Git Credential Manager**. Keep the other defaults. Without Git Credential
   Manager, clone asks for a password every time.
2. Install **VS Code**. Open **Extensions** (the four-blocks icon on the left). Search for `Azure`, install
   **Azure Resources**, and keep auto update on.
3. Restart VS Code. Press Ctrl+Shift+P, type `Azure`, pick the sign-in command, and accept in the browser. The
   sign-in lasts. You rarely sign in again.
4. Create `C:\git`. Never put repositories in OneDrive or in a path with spaces. If VS Code or Git reports
   access denied there, do this: open File Explorer, right-click `C:\git`, select **Properties**, then
   **Security**, then **Edit**. Select **Users**, check **Full control**, and select **OK**.
5. In Azure Repos, open the repository, select **Clone**, then **Clone in VS Code**. Pick `C:\git`. If it asks
   for a password, Git Credential Manager is missing. Rerun the Git installer and add it.
6. In the VS Code terminal (**Terminal > New Terminal**), set your identity. Run
   `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`, using
   your work email. Check the result with `git config --global -l`. Press q to leave the list.

## Daily loop

1. Edit files. A white dot on a tab means unsaved changes. Press Ctrl+S to save.
2. Open the **Source Control** view (the branch icon on the left). It shows the count of changed files. Click
   each changed file to check its diff.
3. Type a commit message and select **Commit**. When asked, choose **Always** to stage all changes.
4. Prefer a branch and a pull request. Select **Sync Changes** to push. A push to `main` starts the app
   pipeline. See [App](/Pipelines/App).

## Unpack and pack an exported app

1. Drag the `.tgz` file into the package folder.
2. Right-click the file and select **Open in Integrated Terminal**.
3. To unpack, run `tar xf <file>.tgz`. To pack a folder, run `tar czf <file>.tgz <folder>`.
