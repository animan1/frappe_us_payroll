# Frappe US Payroll

Frappe US Payroll is an open-source US payroll calculation and localization layer for Frappe HR.
Frappe HR remains responsible for payroll workflow and Salary Slips; this app supplies the missing US
deduction, liability, employee-configuration, YTD, and reporting integration.

The initial scope is federal payroll. Filing, remittance, direct deposit, scheduling, time clocks, and general
HR functionality are intentionally out of scope.

## Payroll setup

The app marks existing and new earning Salary Components as **Subject to US Social Security** by default. Review
every earning component during initial setup and whenever a component is added. Leave ordinary wage components,
including Frappe HR's standard `Basic` component, checked.

Uncheck **Subject to US Social Security** only when the component represents a payment excluded from Social
Security wages. For example, qualifying business-expense reimbursements under an accountable plan are excluded,
while payments under a nonaccountable plan are wages. See [IRS Publication 15, section 5 and the special-payment
table](https://www.irs.gov/publications/p15) and confirm uncertain classifications with the employer's tax
professional. Later migrations preserve deliberate exclusions.

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

## License

Frappe US Payroll is licensed under GPL-3.0. Frappe Framework itself is MIT-licensed, while the ERPNext and
Frappe HR applications this project integrates with are GPL-3.0. Using GPL-3.0 keeps the complete dependency
stack license-compatible; the choice is not imposed by Frappe Framework alone.

## Current state

The Social Security calculator and its Frappe data fields are implemented. The Salary Slip regional hook remains
inert until the calculator-to-component adapter is connected.
