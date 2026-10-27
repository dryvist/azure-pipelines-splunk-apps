# Build Service

One time. Done at project setup; you should not need this again.

Grant the project Build Service the rights that the Onboard pipeline needs. Grant the rights that each app
repository needs.

## Project rights for Onboard

1. Open the project and select **Project settings**.
2. Select **Pipelines**, then **More actions**, then **Manage security**.
3. Select `<project> Build Service (<organization>)`. Set **Create build pipeline** to **Allow**.

The Onboard pipeline also needs the Build Service to have **Administer** or **User** on the variable groups
and environments. It also needs **Administer** on the `tools` repository.

## App repository

Grant these rights on each new app repository before you run Onboard.

1. Open **Project settings → Repositories**, select the app repository, then select **Security**.
2. Find `<project> Build Service (<org>)`.
3. Allow **Contribute**, **Contribute to pull requests**, and **Create tag**.

What each right does:

- **Contribute** pushes the version bump and the import branch.
- **Contribute to pull requests** creates the import pull request.
- **Create tag** pushes `v<version>` in the Release stage.

Verify that each of the three rights shows **Allow** for the app repository's Build Service identity.
