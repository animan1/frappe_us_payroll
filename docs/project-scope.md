# Project scope

## Goal

Provide the missing US calculation and localization layer that allows Frappe HR to replace TimeTrex Community
Cloud for Crane's Castle Brewing and to serve as a generally useful open-source Frappe integration.

Frappe HR owns payroll workflow and Salary Slips. A generic tax library should own federal calculations where a
healthy upstream exists. This app is the tested bridge between them, plus regional functionality without a better
upstream home.

## Initial deliverables

- Correct employee deductions and employer liabilities.
- Useful native Frappe Salary Slips and pay stubs.
- Employee configuration and YTD/opening state needed for correct calculations.
- Aggregate component reporting sufficient to prepare federal and Washington filings manually.
- Deterministic regression tests against de-identified TimeTrex payroll results and authoritative agency examples.

## First jurisdictions

- Federal income-tax withholding, Social Security, Medicare, Additional Medicare, and FUTA.
- Washington PFML, WA Cares, unemployment, and L&I/workers' compensation after the federal adapter is proven.

## Explicitly out of scope

- Tax e-filing and automated remittance.
- Direct deposit and payroll ACH.
- Scheduling and time clocks.
- General HR features already supplied by Frappe HR.
- A generic 50-state framework in the initial implementation.
- Bulk import of historical payroll that is not needed for cutover calculations or reporting.

## System-of-record boundary

TimeTrex, GnuCash, archived reports, and filings remain the historical system of record. Frappe becomes the payroll
system of record from cutover forward. Only the 2026 YTD/opening values necessary for correct midyear calculations
and reporting should be imported.

GnuCash remains the authoritative business accounting system.
