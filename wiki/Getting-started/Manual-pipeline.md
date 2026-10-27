# Manual pipeline setup

Use these steps to create a manual pipeline from the name and YAML path on its setup page.

1. Open **Pipelines**.
2. Select **New pipeline**.
3. Select **Azure Repos Git**.
4. Select the repository containing the YAML file.
5. Select **Existing Azure Pipelines YAML file**.
6. Select branch `main`.
7. Select the YAML path shown on the setup page.
8. Select **Continue**.
9. Enter the pipeline name shown on the setup page.
10. Select the arrow next to **Save & run**.
11. Select **Save**.
12. Select **Edit**.
13. Select **⋮** (More actions).
14. Select **Triggers**.
15. Select the **YAML** tab.
16. Select **Default agent pool for YAML**.
17. Select the configured pool.
18. Select the arrow next to **Save & queue**.
19. Select **Save**.
20. Confirm the pipeline appears under **Pipelines** with no runs.

If resource access fails, follow [Permissions troubleshooting](/Troubleshooting/Permissions).
