# Frappe US Payroll

Frappe US Payroll is an open-source US payroll calculation and localization layer for Frappe HR.
Frappe HR remains responsible for payroll workflow and Salary Slips; this app supplies the missing US
deduction, liability, employee-configuration, YTD, and reporting integration.

The initial scope is federal payroll. Filing, remittance, direct deposit, scheduling, time clocks, and general
HR functionality are intentionally out of scope.

## Development

The local development environment extends HRMS's Docker Compose configuration. The repository is bind-mounted
into the Frappe container, and a named volume preserves the bench. Run `make help` for the supported developer
operations. In particular:

```console
make up
make ps
make install
make check
make test
```

`make install` is a one-time site operation. Use `make migrate` after subsequent model or fixture changes.
Changes in the working tree are immediately visible through the bind mount. `make test` runs the app's Frappe
test suite.

Run `make deps-lock` after intentionally changing dependencies, and commit the resulting `uv.lock`. Normal
development and CI use `make deps` through the verification targets and refuse to change the lock.

### UI integration smoke test

Run `make enable-ui-smoke` to create the `US Payroll Integration Test` deduction and enable its explicit
development-site behavior. Add that component to a Salary Structure with an amount of zero, then generate or
recalculate a Salary Slip. The app will replace the amount with `$12.34` before HRMS finalizes totals.

Run `make disable-ui-smoke` when finished. Disabling leaves the Salary Component in place because Frappe may have
linked it from Salary Structures or test Salary Slips, but it stops changing any amounts. While enabled, a Salary
Slip missing the component fails validation instead of silently omitting the deduction.

## License

Frappe US Payroll is licensed under GPL-3.0. Frappe Framework itself is MIT-licensed, while the ERPNext and
Frappe HR applications this project integrates with are GPL-3.0. Using GPL-3.0 keeps the complete dependency
stack license-compatible; the choice is not imposed by Frappe Framework alone.

## Current state

The first integration slice turns the proven `$12.34` Salary Slip experiment into an automated test and an
explicitly opt-in development-site UI check. The production hook remains inert unless UI smoke mode is enabled;
no real federal calculator is connected yet.
