# Frappe US Payroll

Frappe US Payroll is an open-source US payroll calculation and localization layer for Frappe HR.
Frappe HR remains responsible for payroll workflow and Salary Slips; this app supplies the missing US
deduction, liability, employee-configuration, YTD, and reporting integration.

The initial scope is federal payroll plus Washington-specific requirements. Filing, remittance, direct
deposit, scheduling, time clocks, and general HR functionality are intentionally out of scope.

## Development

The local development environment uses the existing `hrms.localhost` bench containers. Run `make help`
for the supported developer operations. In particular:

```console
make up
make ps
make install
make check
make test
```

`make install` is a one-time site operation. Use `make migrate` after subsequent model or fixture changes.
`make test` synchronizes the working tree into the existing bench and runs the app's Frappe test suite.

### UI integration smoke test

Run `make enable-ui-smoke` to create the `US Payroll Integration Test` deduction and enable its explicit
development-site behavior. Add that component to a Salary Structure with an amount of zero, then generate or
recalculate a Salary Slip. The app will replace the amount with `$12.34` before HRMS finalizes totals.

Run `make disable-ui-smoke` when finished. Disabling leaves the Salary Component in place because Frappe may have
linked it from Salary Structures or test Salary Slips, but it stops changing any amounts.

## Current state

The first integration slice turns the proven `$12.34` Salary Slip experiment into an automated test and an
explicitly opt-in development-site UI check. The production hook remains inert unless UI smoke mode is enabled;
no real federal calculator is connected yet.

This is foundation work, not a production tax calculator.
