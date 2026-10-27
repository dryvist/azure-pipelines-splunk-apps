# Edit files in the browser

Use the Azure Repos web UI to change one file. Commit the change to a new branch, then merge it through a
pull request. Use this page first. Use [VS Code](/Editing/VS-Code) for folder work.

The browser cannot upload a folder. A change that adds or replaces a folder, such as a new `package/`, goes
through VS Code.

1. Open **Repos → Files** in the project. Select the repository that contains the file.
2. Select the file.
3. Select **Edit**.
4. Change the file.
5. Select **Commit**. Choose the option to commit to a new branch, and start a pull request.
6. Open the pull request. Select **Complete** to merge it into `main`.

Merging to `main` in an app repository starts the app pipeline. See [App](/Pipelines/App).
