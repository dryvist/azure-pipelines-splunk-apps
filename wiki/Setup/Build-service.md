# Build Service

One time. Done at project setup; you should not need this again.

Grant the project Build Service the rights that the Onboard pipeline needs. Grant the rights that each app
repository needs.

## Project rights for Onboard

1. Open the project and select **Project settings**.
2. Select **Pipelines**, then **More actions**, then **Manage security**.
3. Select `<project> Build Service (<organization>)`. Set **Create build pipeline** to **Allow**.

Onboard adds each new app pipeline to the **Pipeline permissions** of every variable group and environment.
That needs the **Administrator** role. **User** is not enough.

1. Open **Pipelines → Environments**, then `splunk-nonprod`.
2. Select **⋮**, then **Security**.
3. Under **User permissions**, add `<project> Build Service (<organization>)` with the **Administrator** role.
4. Repeat steps 1 to 3 for `splunk-prod`.
5. Open **Pipelines → Library**, then the `splunk-nonprod` variable group.
6. Select **Security**. Add `<project> Build Service (<organization>)` with the **Administrator** role.
7. Repeat steps 5 and 6 for `splunk-appinspect`, `splunk-itsi-nonprod`, `splunk-prod`, and `splunk-itsi-prod`.

Onboard also needs **Administer** on the `tools` repository.

If Onboard warns that it could not authorize a resource, open that resource and add the new app pipeline under
**Pipeline permissions**.

## App repository

Grant these rights once for all repositories before you run Onboard. New repositories inherit them.

1. Open **Project settings → Repositories**, then select **Security** at the top. To grant one repository only,
   select it first.
2. Find `<project> Build Service (<org>)`.
3. Allow **Contribute**, **Contribute to pull requests**, and **Create tag**.

What each right does:

- **Contribute** pushes the version bump and the import branch.
- **Contribute to pull requests** creates the import pull request.
- **Create tag** pushes `v<version>` in the Release stage.

Verify that each of the three rights shows **Allow** for the app repository's Build Service identity.
