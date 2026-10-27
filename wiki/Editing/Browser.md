# Edit files in the browser

Use the Azure Repos web UI to change one file. Commit the change to a new branch, then merge it through a
pull request. Use this page first. Use [VS Code](/Editing/VS-Code) for folder work.

The browser cannot upload a folder. A change that adds or replaces a folder, such as a new `package/`, goes
through VS Code.

1. Open **Repos → Files** in the project. Select the repository that contains the file.
2. Select the file.
3. Select **Edit**.
4. Change the file.
5. Select **Commit**.
6. Select **Create a new branch** and keep **Create a pull request** checked.
7. Select **Commit** again.
8. Select **Create** on the pull request.
9. When checks pass, select **Complete**.

Merging to `main` in an app repository starts the app pipeline. See [App](/Pipelines/App).
