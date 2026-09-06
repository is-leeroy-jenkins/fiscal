# Full-Time Equivalents

Fiscal implements the two civilian full-time-equivalent (FTE) calculation methods in section 85 of
[OMB Circular No. A-11 (2025)](https://www.whitehouse.gov/wp-content/uploads/2025/08/s85.pdf).
An FTE is an hours-based work-year measure, not an employee headcount.

## Qualifying hours

Both methods use regular straight-time hours. Prepare the numerator before passing it to Fiscal:

| Include | Exclude |
| --- | --- |
| Regular straight-time hours worked | Overtime |
| Annual leave | Holiday hours worked |
| Sick leave | Terminal leave |
| Compensatory time off | Active-duty military personnel |
| Other approved leave | Workload-planning deductions |

OMB treats approved leave as hours worked for budgetary FTE reporting. This differs from an
`available workhours` workload model, which may subtract leave, training, and other non-work time.
Do not use one measure as a substitute for the other.

## Regular method

The regular method covers October 1 through September 30:

**FTE = regular straight-time hours / (Monday–Friday days in the fiscal year × 8)**

Federal holidays do not reduce the denominator. Depending on the calendar, an eight-hour federal
workday produces 2,080, 2,088, or 2,096 compensable hours.

```python
from fiscal import FullTimeEquivalent

calculator = FullTimeEquivalent( 2026 )

print( calculator.compensable_days )   # 261
print( calculator.compensable_hours )  # Decimal('2088')
print( calculator.regular_method( 1044 ) )  # Decimal('0.5')
```

Fiscal derives the denominator from the calendar rather than limiting calculations to years already
stored in the SQLite database.

For part of a fiscal year, use the same weekday-based denominator through
`FiscalYear.compensable_hours_between()`:

```python
from fiscal import FiscalYear

fiscal_year = FiscalYear( 2026 )
hours = fiscal_year.compensable_hours_between(
    start="2026-07-01",
    end="2026-07-31",
)
```

This method includes weekday holidays. Use `FiscalYear.work_hours_between()` when the required result
is scheduled operational hours after excluding federal holidays.

## Pay-period method

The pay-period method uses the 26 biweekly pay periods ending in the fiscal year:

**FTE = regular straight-time hours in the selected pay periods / 2,080**

```python
calculator = FullTimeEquivalent( 2026 )
print( calculator.pay_period_method( 1040 ) )  # Decimal('0.5')
```

When 27 pay periods end in a fiscal year, OMB requires the agency to omit the period containing the
fewest workdays in that fiscal year. Supply Fiscal with the already-selected 26-period hours total;
the calculator cannot infer pay-period boundaries from an aggregate value.

## Planning hours from FTEs

The inverse helpers convert an FTE amount into the hours required by either method:

```python
calculator = FullTimeEquivalent( 2026 )

regular_hours = calculator.hours_for_regular_fte( 1.5 )
pay_period_hours = calculator.hours_for_pay_period_fte( 1.5 )
```

Results use `Decimal` and are not forcibly rounded. Apply the precision and presentation rules
required by the receiving budget system only after calculation.

## Reporting boundaries

The arithmetic is the same for direct, reimbursable, and allocation civilian FTEs, but their Schedule
Q reporting lines and responsible accounts differ. Fiscal does not decide which category owns a set
of hours. OMB also directs agencies to report active-duty military personnel as average strength,
not FTEs.

Additional federal references:

- [GAO, *A Glossary of Terms Used in the Federal Budget Process*](https://www.gao.gov/assets/gao-05-734sp.pdf)
- [GAO-20-148, *Civilian Personnel*](https://www.gao.gov/assets/710/702141.pdf)
- [Congressional Research Service, *Federal Workforce Statistics Sources: OPM and OMB*](https://www.congress.gov/crs_external_products/R/PDF/R43590/R43590.17.pdf)
- [FY 2027 Budget Appendix examples on GovInfo](https://www.govinfo.gov/content/pkg/BUDGET-2027-APP/pdf/BUDGET-2027-APP-2-14.pdf)
