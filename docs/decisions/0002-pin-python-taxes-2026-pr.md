# ADR 0002: Temporarily pin the reviewed `python-taxes` 2026 revision

- Status: Accepted
- Date: 2026-08-20

## Context

The latest `python-taxes` release supports tax years only through 2025. Upstream pull request #1 adds the 2026
Publication 15-T schedules and the 2026 Social Security wage base, but it has not been reviewed or released by
the upstream maintainer.

The project should exercise the upstream calculation API without copying its federal tax engine into this
repository. A moving branch or pull-request reference would make payroll results change without a dependency
review.

## Decision

Pin `python-taxes` to commit `631ba1eca6f613fd3ec3cc4ada7d8e844308a71c` from the pull-request author's fork.
The pinned source remains an external MIT-licensed dependency. It is not vendored or modified here.

The Frappe-independent adapter exposes separate employee-withholding and employer-liability results. It accepts
Social Security taxable wages explicitly; it does not assume that HRMS gross pay is taxable wages.

## Verification

Regression tests verify the 2026 employee and employer rate, the `$184,500` wage base, the `$11,439.00` maximum
share, a pay period crossing the wage base, and a pay period after the limit. These values are published in IRS
Publication 15 (2026) and by the Social Security Administration.

## Consequences

- Dependency updates require an explicit commit change and deterministic payroll regression review.
- The pin should move to an upstream release after 2026 support is merged and published.
- If upstream remains unresponsive, a maintained fork requires a separate governance decision and exit plan.
- Salary Slip integration remains blocked on explicit Social Security taxable-wage classification and prior-YTD
  retrieval; HRMS gross pay must not be substituted implicitly.
