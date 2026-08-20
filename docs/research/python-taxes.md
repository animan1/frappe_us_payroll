# `python-taxes` suitability assessment

- Assessment date: 2026-08-20
- Upstream repository: <https://github.com/stacynoland/python-taxes>
- PyPI package: <https://pypi.org/project/python-taxes/>
- 2026 support pull request: <https://github.com/stacynoland/python-taxes/pull/1>

## Preliminary recommendation

Treat `python-taxes` as the preferred upstream home for generic federal payroll calculations, but do not yet
make its current PyPI release a production dependency. Help upstream merge and harden 2026 support first, add
missing boundary tests and fixes, and pin a reviewed release only after it reproduces authoritative IRS examples
and de-identified TimeTrex payroll cases.

This is still preferable to immediately creating a second federal calculation engine in this app.

## 1. Project health

The project is small and young. It was created in March 2025, has one primary contributor, and published seven
releases through `0.7.0` in October 2025. The last source commit on the default branch was October 20, 2025.
Automated tests passed for that source commit, while later dependency-update runs have failed.

The open 2026 pull request was created March 12, 2026. As of this assessment it is cleanly mergeable but has no
maintainer review, discussion, or recorded check runs. The lack of response for five months creates stewardship
risk, but the repository is not archived and its scope aligns unusually well with this project.

## 2. License compatibility

The package is MIT licensed. MIT code can be used as a dependency of a GPL Frappe application. No vendoring is
needed or desired.

## 3. Test coverage

The default branch has unit tests for federal income withholding, Social Security, Medicare, and the CLI. The
calculation cases are stored only under a `tests/2024` tree even though source tables cover 2023 through 2025.
There are numerous ordinary-value tests, but important payroll boundaries are missing.

The 2026 pull request adds 50 tests for its PDF/Federal Register updater and source generation. It does not add a
parallel suite of direct 2025 and 2026 calculator regression cases covering all filing statuses and threshold
boundaries. The pull request also has no recorded CI check runs.

## 4. Current W-4 model and API

There is no durable W-4 domain model. `income.employer_withholding()` accepts flat arguments corresponding to a
2020-or-later W-4:

- filing status;
- Step 2 multiple-jobs checkbox;
- Step 3 credits;
- Step 4(a) other income;
- Step 4(b) deductions; and
- Step 4(c) extra withholding.

A separate `employer_withholding_pre_2020()` function accepts marital status, allowances, and extra withholding.
The API uses `Decimal`, Pydantic validation, string literals for filing status and pay frequency, and returns one
withholding amount.

The flat API is adequate for a thin adapter, but the Frappe app must own effective dating, W-4 provenance,
exemption state, employee configuration, and any unsupported cases such as nonresident-alien adjustments or
supplemental-wage methods.

## 5. Publication 15-T implementation

The library implements the percentage method for automated payroll systems. It annualizes period wages, applies
W-4 adjustments, selects a filing-status/multiple-jobs schedule, de-annualizes the result, applies credits and
extra withholding, and rounds with `ROUND_HALF_UP`.

The brackets live in three Python modules (`single`, `married`, and head-of-household), each containing standard
and multiple-jobs schedules keyed by tax year. This is readable but data-heavy. The open pull request adds a tool
to regenerate and structurally validate these tables from IRS Publication 15-T.

The calculation code currently constructs some percentages through a binary float before converting to
`Decimal`. Cent quantization usually masks this, but an upstream cleanup should construct rates entirely from
decimal strings or integers.

## 6. Tax-year architecture

Supported years are repeated across a current-year constant, a validation list, income schedule dictionaries,
and the Social Security wage-base dictionary. Medicare rates and thresholds are not year-versioned. Unsupported
years fail validation or dictionary lookup.

The architecture is simple enough to extend but does not yet guarantee that all annual parameters move together.
The pull request's updater is a meaningful improvement, provided its downloaded-source tests are complemented by
checked-in deterministic expected values.

## 7. Difficulty of adding 2026

The mechanical 2026 update is modest: six Publication 15-T schedules, the valid/current-year constants, and the
Social Security wage base. Pull request #1 already supplies these changes and an updater. Its values still need
independent verification against final IRS sources and direct calculator regression tests.

Adding 2026 does not address broader gaps:

- FUTA is not implemented.
- Employee and employer liabilities are not modeled separately.
- `medicare.required_withholding()` over-withholds when a pay period crosses the `$200,000` Additional Medicare
  threshold because it applies the additional rate to the entire period rather than only wages above the
  threshold.
- The filing-status thresholds in `medicare.additional_withholding()` describe an individual's eventual tax
  threshold, not the employer's mandatory `$200,000` withholding trigger, so the API naming can invite misuse.
- Supplemental wage methods, nonresident-alien adjustments, and W-4 exemption handling are absent.

## 8. Upstream contribution feasibility

Contribution is technically realistic: the codebase is small, MIT licensed, typed, and already has a focused
2026 pull request. The main uncertainty is governance responsiveness rather than implementation difficulty.

Recommended upstream sequence:

1. Review pull request #1 against final 2026 Publication 15-T and Social Security sources.
2. Ask the maintainer whether they intend to merge/release it and welcome additional maintainers.
3. Add deterministic 2025/2026 calculation examples and bracket-boundary tests.
4. Fix Additional Medicare threshold-crossing behavior in a narrowly scoped pull request.
5. Clarify employee withholding versus employer liability APIs.
6. Add FUTA only after its input/output contract and wage-category requirements are specified.

If upstream remains unresponsive, use a temporary pinned Git revision or maintained fork only with an explicit
ADR and exit plan. Do not copy the source into `frappe_us_payroll`.
