# ADR 0001: Use the HRMS regional Salary Slip deduction hook

- Status: Accepted
- Date: 2026-08-20

## Context

US statutory deductions must be calculated after HRMS has resolved Salary Structure earnings and ordinary
deductions, but before it finalizes Salary Slip totals. A `Salary Slip.validate` document event was proven to
support mutation, but it executes after the controller's `validate` method has already calculated net pay and
YTD fields. A generic validation event would therefore need to recalculate derived fields and would depend on
more of HRMS's internal lifecycle.

HRMS added `SalarySlip.apply_regional_deductions()` on June 25, 2026. The method is called by
`calculate_net_pay()` after earnings, Salary Structure deductions, and loan repayment are resolved, and before
precision and net-pay totals are finalized. The method uses HRMS's supported `regional_overrides` hook.

The hook is present on the upstream `develop`, `version-16`, and `version-16-hotfix` lines inspected for this
decision. The relevant upstream commits are `04f5029ea` on `develop` and `d92f19d3d` on version 16.

## Decision

Register a `regional_overrides` entry for `United States` mapping
`hrms.payroll.doctype.salary_slip.salary_slip.apply_regional_deductions` to the Frappe US Payroll adapter.

The adapter will mutate Salary Slip components only. HRMS remains responsible for precision, deduction totals,
net pay, currency conversion, pay-stub rendering, submission workflow, and its native YTD component aggregation.

The production adapter remains inert until a real calculator is connected. An integration test enables the
proven `$12.34` fixture through the registered hook and verifies HRMS's native totals. The same behavior can be
enabled explicitly on a development site for UI verification; it is disabled by default and clearly named as an
integration test rather than a payroll rule.

## Consequences

- No HRMS fork or DocType-class override is required.
- Deductions participate in native Salary Slip totals and component-wise YTD computation.
- The minimum supported HRMS version must contain the June 25, 2026 regional hook.
- Company-country dispatch currently depends on HRMS's regional context resolution. Tests must cover the actual
  site configuration, especially if a deployment later contains companies from more than one country.
- Employer-only liabilities will need durable Salary Slip-linked records or statistical/accrual components;
  they must not be represented as employee deductions merely to reuse this hook.

## Alternatives considered

- `doc_events` on `validate`: proven for mutation, but too late in the controller lifecycle for clean totals and
  YTD calculation.
- `override_doctype_class`: substantially broader coupling than required and more likely to conflict with other
  apps.
- HRMS fork: rejected because the required supported extension point exists upstream.
