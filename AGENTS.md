# Contributor instructions

These instructions apply to all work in this repository.

## Scope and architecture

1. Treat Frappe, ERPNext, and HRMS as upstream dependencies. Inspect them freely, but do not modify them from this repository or require an HRMS fork.
2. Keep generic federal tax calculations outside the Frappe adapter wherever practical. Prefer contributing generic fixes and annual data to `python-taxes`.
3. Do not vendor or copy `python-taxes` into this repository.
4. Keep this app focused on Frappe integration, employee tax configuration, YTD retrieval, component mapping, reporting, and deliberately scoped jurisdictional extensions.
5. Do not add filing, remittance, direct-deposit, ACH, scheduling, time-clock, or general-HR functionality without an explicit scope decision.
6. Do not build a generic 50-state framework before concrete implementations demonstrate a useful abstraction.
7. Build aggregate reporting from submitted Salary Slip components rather than creating a separate accounting system.
8. Treat archived TimeTrex records as a test oracle and Frappe as the system of record from cutover forward.

## Workflow

1. Use the Makefile for repeatable development, environment, installation, and verification operations. Reserve ad hoc commands for genuine one-time inspection or diagnosis.
2. Prefer small, reviewable changes and deterministic regression tests.
3. Do not add a dependency without documenting its purpose and maintenance implications.
4. Record significant architectural decisions in `docs/decisions/`.
5. Record deferred work rather than silently expanding scope.
6. Keep secrets and employee payroll data out of the repository and Git history. Test fixtures derived from real payroll must be minimized and de-identified.
7. Never commit or push directly to `main`. Use a feature branch and a pull request; append commits after publication rather than rewriting published history.
8. Do not claim a payroll calculation is correct without an authoritative source and deterministic tests, including threshold-boundary cases where applicable.
9. For executable changes, include reviewer exercise instructions in the pull request body: prerequisites, concrete commands or UI steps, and the expected result.

## Completion report

Report work completed, files changed, validation performed or not performed, assumptions, open questions, and the smallest recommended next step.
