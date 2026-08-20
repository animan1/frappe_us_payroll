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

## License

Frappe US Payroll is licensed under GPL-3.0. Frappe Framework itself is MIT-licensed, while the ERPNext and
Frappe HR applications this project integrates with are GPL-3.0. Using GPL-3.0 keeps the complete dependency
stack license-compatible; the choice is not imposed by Frappe Framework alone.

## Current state

This change establishes the app and repeatable development workflow. It does not yet add payroll calculations.
