# Project scope

## Goal

Provide the missing US calculation and localization layer that allows Frappe HR to serve as a generally useful
open-source payroll system in the United States.

Frappe HR owns payroll workflow and Salary Slips. A generic tax library should own federal calculations where a
healthy upstream exists. This app is the tested bridge between them, plus regional functionality without a better
upstream home.

## Initial deliverables

- Correct employee deductions and employer liabilities.
- Useful native Frappe Salary Slips and pay stubs.
- Employee configuration and YTD/opening state needed for correct calculations.
- Aggregate component reporting sufficient to prepare payroll tax filings manually.
- Deterministic regression tests against de-identified TimeTrex payroll results and authoritative agency examples.

## Initial tax scope

- Federal income-tax withholding, Social Security, Medicare, Additional Medicare, and FUTA.

## Explicitly out of scope

- Tax e-filing and automated remittance.
- Direct deposit and payroll ACH.
- Scheduling and time clocks.
- General HR features already supplied by Frappe HR.
- A generic 50-state framework in the initial implementation.
- Bulk import of historical payroll that is not needed for cutover calculations or reporting.

## System-of-record boundary

Existing payroll systems, archived reports, and submitted filings remain the historical system of record. Frappe
becomes the payroll system of record from cutover forward. Only the tax-year YTD/opening values necessary for
correct midyear calculations and reporting should be imported.
