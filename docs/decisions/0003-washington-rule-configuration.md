# Decision 0003: Separate statewide Washington rules from employer rates

## Status

Accepted.

## Context

Washington payroll combines annual statewide parameters with inputs assigned to a particular employer. Treating
all of them as hard-coded constants would force a release for every experience-rate change. Treating all of them
as free-form configuration would make statutory updates easy to miss and hard to test.

For 2026:

- Paid Leave has a 1.13% total premium, a 71.43% employee share, a 28.57% employer share, and the federal Social
  Security wage cap of $184,500. Employers with fewer than 50 employees are not required to pay the employer
  share. Tips are excluded. Sources: [WA Paid Leave updates](https://paidleave.wa.gov/updates/) and the
  [employer toolkit](https://paidleave.wa.gov/app/uploads/2021/12/Employer-Wage-Reporting-and-Premiums-Toolkit-v24.1-2025.12.12.pdf).
- WA Cares is an employee premium of 0.58%, uses the Paid Leave wage definition, and has no Social Security wage
  cap. Source: [WA Cares employer FAQ](https://wacaresfund.wa.gov/toolkit/faq).
- WA unemployment has a $78,200 taxable wage base, but the rate is employer-specific. Source:
  [Employment Security Department tax rates](https://esd.wa.gov/employer-requirements/unemployment-taxes/how-we-determine-tax-rates).
- L&I premiums are calculated from hours and business/risk-classification rates, including the employer's
  experience factor. Sources: [L&I rates](https://www.lni.wa.gov/insurance/rates-risk-classes/rates-for-workers-compensation/)
  and [premium calculations](https://www.lni.wa.gov/insurance/rates-risk-classes/rates-for-workers-compensation/calculating-premium-rates).

## Decision

Version statewide annual rates and wage bases as deterministic rules that reject unsupported years. Store the
employer-specific unemployment percentage, separate employee/employer L&I hourly rates, and Paid Leave employer
share election on the effective-dated Salary Structure Assignment.

Use explicit Employee exemption flags for Paid Leave and WA Cares. Use Salary Component taxability flags to
identify wages included in Paid Leave/WA Cares and unemployment; this keeps tips and future earning categories
data-driven without building a generic 50-state framework.

Enable Washington calculation explicitly per Salary Structure Assignment. When disabled, federal calculation
continues without requiring Washington components or configuration.

## Consequences

- Annual statutory updates are reviewable code and can carry authoritative boundary tests.
- Employer rate changes take effect through a new Salary Structure Assignment rather than an application release.
- Existing earning components must be reviewed after installation, especially tips.
- The first implementation supports one pair of L&I hourly rates per assignment. Employees splitting work across
  multiple risk classes require a later, evidence-driven model rather than a premature generic abstraction.
