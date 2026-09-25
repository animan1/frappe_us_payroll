# Frappe US Payroll

Frappe US Payroll is an open-source US payroll calculation and localization layer for Frappe HR.
Frappe HR remains responsible for payroll workflow and Salary Slips; this app supplies the missing US
deduction, liability, employee-configuration, YTD, and reporting integration.

The initial scope is federal and Washington payroll. Filing, remittance, direct deposit, scheduling, time clocks,
and general HR functionality are intentionally out of scope.

## Payroll setup

The app marks existing and new earning Salary Components as taxable by default for Social Security, federal
income tax, Medicare, FUTA, WA Paid Leave/WA Cares, and WA unemployment. Review every earning component during
initial setup and whenever a component is added. Leave ordinary wage components, including Frappe HR's standard
`Basic` component, checked.

Uncheck **Subject to US Social Security** only when the component represents a payment excluded from Social
Security wages. For example, qualifying business-expense reimbursements under an accountable plan are excluded,
while payments under a nonaccountable plan are wages. See [IRS Publication 15, section 5 and the special-payment
table](https://www.irs.gov/publications/p15) and confirm uncertain classifications with the employer's tax
professional. Later migrations preserve deliberate exclusions.

For Washington payroll:

1. Uncheck **Subject to WA Paid Leave and WA Cares** for tips and any other excluded earnings.
2. Add the app-owned federal and Washington deduction and employer-contribution components to the applicable
   Salary Structure. Their amounts should start at zero; the app replaces them during calculation.
3. Create a new effective-dated Salary Structure Assignment, enable **Calculate Washington Payroll**, and enter
   the employer's current WA unemployment percentage and employee/employer L&I hourly rates.
4. Enable **Pay WA Paid Leave Employer Share** only when the employer owes or has elected to pay that share.
5. Record any individual Paid Leave or WA Cares exemption on the Employee.

The statewide 2026 Paid Leave, WA Cares, and unemployment wage-base rules are versioned in code and fail closed
for unsupported years. Employer-specific unemployment and L&I rates remain effective-dated assignment inputs.
See the [Washington payroll decision](docs/decisions/0003-washington-rule-configuration.md) for sources and the
reason for this boundary.

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
Changes in the working tree are immediately visible through the bind mount. `make test` provisions and runs on
`frappe-us-payroll.localhost`; it does not enable tests on `hrms.localhost`.

Run `make e2e-demo` to build browser assets and create a persistent $1,000 draft Salary Slip on the isolated site.
Open `http://frappe-us-payroll.localhost:8000`, sign in as `Administrator` with the default development password
`Administrator`, and inspect the returned Salary Slip. Editing its Basic earning should refresh employee
deductions, employer contributions, taxable wages, and net pay without saving first.

Run `make deps-lock` after intentionally changing dependencies, and commit the resulting `uv.lock`. Normal
development and CI use `make deps` through the verification targets and refuse to change the lock.

## License

Frappe US Payroll is licensed under GPL-3.0. Frappe Framework itself is MIT-licensed, while the ERPNext and
Frappe HR applications this project integrates with are GPL-3.0. Using GPL-3.0 keeps the complete dependency
stack license-compatible; the choice is not imposed by Frappe Framework alone.

## Current state

The Salary Slip regional hook calculates federal income-tax withholding, employee and employer Social Security,
employee and employer Medicare, FUTA, WA Paid Leave, WA Cares, WA unemployment, and hourly WA L&I. Submitted
Salary Slips supply annual wage-limit state.
