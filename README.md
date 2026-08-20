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

## Current state

The first integration slice turns the proven `$12.34` Salary Slip experiment into an automated test. The test
injects a fixed deduction through HRMS's regional override hook and verifies native deduction and net-pay totals.
The production hook remains inert until the first real federal calculation is connected.

This is foundation work, not a production tax calculator.
