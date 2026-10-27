# Edit files in VS Code

Use VS Code to clone a repository, change folders, and commit from a local copy. For a single file, use
[Edit files in the browser](/Editing/Browser) instead.

## One time per workstation

### Install Git

1. Open git-scm.com.
2. Download **Git for Windows**.
3. Run the installer.
4. On the default branch page, select **Override** and enter `main`.
5. On the SSH page, select **Use bundled OpenSSH**.
6. On the credential helper page, select **Git Credential Manager**.
7. Keep every other default and finish the installer.

### Install VS Code and sign in to Azure

1. Install **VS Code**.
2. Open VS Code.
3. Select **Extensions** (the four-blocks icon on the left).
4. Search for `Azure Resources`.
5. Select **Install**.
6. Close VS Code.
7. Open VS Code.
8. Press Ctrl+Shift+P.
9. Type `Azure: Sign In`.
10. Press Enter.
11. Accept the sign-in in the browser.

### Create the repository folder

1. Create the folder `C:\git`. Do not use OneDrive or a path with spaces.
2. If Git later reports access denied in `C:\git`: right-click `C:\git` in File Explorer.
3. Select **Properties**.
4. Select **Security**.
5. Select **Edit**.
6. Select **Users**.
7. Check **Full control**.
8. Select **OK**.

### Set your name and email

1. In VS Code, select **Terminal > New Terminal**.
2. Run `git config --global user.name "Your Name"`.
3. Run `git config --global user.email "you@example.com"` with your work email.
4. Run `git config --global -l` to check both values.
5. Press q to leave the list.

## Clone a repository

1. In Azure Repos, open the repository.
2. Select **Clone**.
3. Select **Clone in VS Code**.
4. Select `C:\git`.
5. If it asks for a password, Git Credential Manager is missing. Rerun the Git installer and select it.

## Change files

1. Select the branch name at the bottom left of VS Code.
2. Select **Create new branch**.
3. Type a branch name and press Enter.
4. Edit files. A white dot on a tab means unsaved changes.
5. Press Ctrl+S.
6. Select **Source Control** (the branch icon on the left).
7. Select each changed file and check its diff.
8. Type a commit message.
9. Select **Commit**. If asked, select **Always** to stage all changes.
10. Select **Publish Branch** (or **Sync Changes** on later commits).
11. In Azure Repos, open the pull request it offers and select **Create**.

Merging the pull request into `main` starts the app pipeline. See [App](/Pipelines/App).

## Unpack or pack an exported app

1. Drag the `.tgz` file into the `package` folder.
2. Right-click the file.
3. Select **Open in Integrated Terminal**.
4. Run `tar xf <file>.tgz` to unpack, or `tar czf <file>.tgz <folder>` to pack.
