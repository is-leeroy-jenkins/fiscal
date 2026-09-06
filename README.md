###### fiscal

![](https://github.com/is-leeroy-jenkins/Fiscal/blob/master/resources/images/github/project-fiscal.png)

<p align="left">
  <a href="#features">Features</a>
  &nbsp;&bull;&nbsp;
  <a href="#installation">Installation</a>
  &nbsp;&bull;&nbsp;
  <a href="#configuration">Configuration</a>
  &nbsp;&bull;&nbsp;
  <a href="#quick-start">Quick Start</a>
  &nbsp;&bull;&nbsp;
  <a href="#api-overview">API Overview</a>
  &nbsp;&bull;&nbsp;
  <a href="https://github.com/is-leeroy-jenkins/Fiscal/blob/master/resources/USER_GUIDE.md">User Guide</a>
  &nbsp;&bull;&nbsp;
  <a href="https://github.com/is-leeroy-jenkins/Fiscal/blob/master/resources/DEVELOPER_GUIDE.md">Developer Guide</a>
  &nbsp;&bull;&nbsp;
  <a href="#license">License</a>
</p>

___

Fiscal is a Python library providing a framework for executing U.S. federal fiscal-year and 
calendar-year calculations. It provides fiscal years and federal holidays with date-range analysis, 
fiscal periods, workday and work-hour calculations, FTE calculations, and actual or observed
federal-holiday handling.

## 📖 Documentation 
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-0078FC?style=for-the-badge&logo=github)](https://is-leeroy-jenkins.github.io/fiscal/)


<a id="features"></a>

## 📝 Features

- SQLite-backed fiscal-year and federal-holiday records
- Fiscal-year lookup by fiscal year, BPOA, and EPOA
- Caller-selected calculation dates for reproducible analysis
- Calendar-year and fiscal-year progress calculations
- Fiscal-month boundaries, names, day counts, week matrices, and rendered calendars
- Plain-text fiscal-month and fiscal-year calendars using `calendar.TextCalendar`
- HTML fiscal-month and fiscal-year calendars using `calendar.HTMLCalendar`
- Fiscal-quarter identification, boundaries, and day counts
- ISO calendar-week and fiscal-week calculations
- Weekday occurrence counts using names such as `"Monday"`
- Fiscal-year date, weekday, weekend, and workday collections
- Monthly weekday, weekend, workday, and holiday summaries
- Actual and observed federal-holiday dates
- Inclusive date-range counts constrained to the represented fiscal year
- Compensable-hour, federal work-hour, and annual FTE calculations for inclusive date ranges
- Elapsed and remaining compensable-hour and federal work-hour calculations
- Holiday range results as native `date` values or ISO strings
- Remaining holiday, workday, and weekend counts
- OMB regular-method and pay-period-method civilian FTE calculations
- Exact decimal FTE results and inverse FTE-to-hours planning calculations
- Leap-day detection
- Fiscal-year and federal-holiday dictionary exports
- Backward-compatible aliases for existing calendar methods
- Operational exception wrapping with `boogr.Error`

<a id="installation"></a>

## 🏗️ Installation

```bash

pip install fiscal-pi

```

The PyPI distribution is named `fiscal-pi`; the installed Python package remains `fiscal`:

```python

import fiscal

```

Install the development dependencies when working from a source checkout:

```bash

pip install -e ".[dev]"

```

<a id="configuration"></a>

## ⚙️ Configuration

Fiscal includes its SQLite data and diagnostic configuration. Override paths with environment
variables only when an application needs external data or log storage:

```bash

DB_PATH=/path/to/fiscal.db
LOG_PATH=/path/to/Exceptions.db

```

<a id="quick-start"></a>

![](https://github.com/is-leeroy-jenkins/fiscal/blob/master/docs/images/fiscal-workflow.png)

___

## 🎯 Quick Start

```python

from datetime import date

from fiscal import FederalHoliday, FiscalYear, FullTimeEquivalent

```

Create a fiscal-year object with a fixed calculation date:

```python

fy = FiscalYear(
    fy=2026,
    current_date=date( 2026, 7, 15 ),
)

```

Using an explicit `current_date` makes fiscal progress calculations reproducible. When omitted, Fiscal uses the current system date.

```python

print( fy.fiscal_year )
print( fy.start_date )
print( fy.end_date )
print( fy.fiscal_month_number( ) )
print( fy.fiscal_quarter_number( ) )
print( fy.fiscal_week_number( ) )
print( fy.fiscal_percent_elapsed( ) )

```

### Fiscal-Year Record

```python

print( fy.bpoa )
print( fy.epoa )
print( fy.expiration_date )
print( fy.cancellation_date )
print( fy.weekdays )
print( fy.weekends )
print( fy.workdays )
print( fy.compensable_days )
print( fy.compensable_workdays )
print( fy.compensable_hours )
print( fy.type )
print( fy.availability )

```

### Full-Time Equivalents

Use OMB's regular method for October-through-September hours and its pay-period method for the 26
selected biweekly pay periods:

```python

fte = FullTimeEquivalent( 2026 )

regular_result = fte.regular_method( 1044 )
pay_period_result = fte.pay_period_method( 1040 )

print( fte.compensable_days )   # 261
print( fte.compensable_hours )  # Decimal('2088')
print( regular_result )         # Decimal('0.5')
print( pay_period_result )      # Decimal('0.5')

```

See the [FTE guide](https://is-leeroy-jenkins.github.io/Fiscal/user-guide/full-time-equivalents/)
for qualifying-hour rules and the 27-pay-period exception.

Multi-year availability:

```python

fy = FiscalYear(
    fy=2026,
    bpoa=2024,
    epoa=2026,
    current_date=date( 2026, 7, 15 ),
)

```

### Calendar and Fiscal Progress

```python

calendar_status = {
    "DayOfYear": fy.calendar_day_of_year( ),
    "DaysElapsed": fy.calendar_days_elapsed( ),
    "DaysRemaining": fy.calendar_days_remaining( ),
    "MonthsElapsed": fy.calendar_months_elapsed( ),
    "MonthsRemaining": fy.calendar_months_remaining( ),
    "PercentElapsed": fy.calendar_percent_elapsed( ),
    "WeekNumber": fy.calendar_week_number( ),
    "MonthName": fy.calendar_month_name( ),
    "WeekdayName": fy.current_weekday_name( ),
}

fiscal_status = {
    "DayOfYear": fy.fiscal_day_of_year( ),
    "DaysElapsed": fy.fiscal_days_elapsed( ),
    "DaysRemaining": fy.fiscal_days_remaining( ),
    "MonthsElapsed": fy.fiscal_months_elapsed( ),
    "MonthsRemaining": fy.fiscal_months_remaining( ),
    "PercentElapsed": fy.fiscal_percent_elapsed( ),
    "MonthNumber": fy.fiscal_month_number( ),
    "QuarterNumber": fy.fiscal_quarter_number( ),
    "WeekNumber": fy.fiscal_week_number( ),
	"CompensableHoursElapsed": fy.compensable_hours_elapsed( ),
	"CompensableHoursRemaining": fy.compensable_hours_remaining( ),
	"WorkHoursElapsed": fy.work_hours_elapsed( ),
	"WorkHoursRemaining": fy.work_hours_remaining( ),
}

```

### Fiscal Months and Quarters

Fiscal months are numbered from October through September.

```python

month_start, month_end = fy.fiscal_month_bounds( 10 )
month_name = fy.fiscal_month_name( 10 )
month_days = fy.fiscal_days_in_month( 10 )
quarter_start, quarter_end = fy.fiscal_quarter_bounds( 4 )
quarter_days = fy.fiscal_days_in_quarter( 4 )

```

Count weekday occurrences without importing `calendar`:

```python

mondays = fy.weekday_occurrences(
    fiscal_month=10,
    weekday="Monday",
)

```

Integer weekday values from `0` through `6` remain supported for compatibility.

### Text and HTML Calendars

Render one fiscal month as plain text:

```python

text_month = fy.fiscal_month_text_calendar(
    fiscal_month=10,
)

```

Render October through September as plain text:

```python

text_year = fy.fiscal_year_text_calendar( )

```

Render one fiscal month as an HTML table:

```python

html_month = fy.fiscal_month_html_calendar(
    fiscal_month=10,
    with_year=True,
)

```

Render the entire fiscal year in rows of three month tables:

```python

html_year = fy.fiscal_year_html_calendar(
    width=3,
)

```

The fiscal-year renderers preserve federal fiscal order from October through September.

### Date-Range Analysis

```python

start_date = date( 2026, 7, 1 )
end_date = date( 2026, 7, 31 )

summary = {
    "WeekendDays": fy.count_weekends(
        start=start_date,
        end=end_date,
    ),
    "FederalHolidays": fy.count_holidays(
        start=start_date,
        end=end_date,
    ),
    "Workdays": fy.count_workdays(
        start=start_date,
        end=end_date,
    ),
    "CompensableHours": fy.compensable_hours_between(
        start=start_date,
        end=end_date,
    ),
    "WorkHours": fy.work_hours_between(
        start=start_date,
        end=end_date,
    ),
	"FTE": fy.fte_between(
		start=start_date,
		end=end_date,
	),
}

```

Range operations are inclusive and constrained to the represented fiscal year. A reversed range or a range that does not intersect the fiscal year raises `boogr.Error`.

`compensable_hours_between()` counts every Monday-through-Friday date, including federal holidays,
consistent with OMB's regular-method denominator. `work_hours_between()` excludes federal holidays
and therefore represents scheduled operational work hours. Both methods accept a positive
`hours_per_day` value and return an exact `Decimal` result.

`fte_between()` divides the range's compensable hours by the selected fiscal year's
`CompensableHours` value. It returns the annual FTE represented by the range, not an annualized rate
for the shorter period. For example, a full FY 2026 at six hours per compensable weekday returns
`Decimal("0.75")`.

```python

part_time_hours = fy.work_hours_between(
    start=start_date,
    end=end_date,
    hours_per_day=6,
)

```

Use actual holiday dates instead of observed dates:

```python

actual_workdays = fy.count_workdays(
    start=start_date,
    end=end_date,
    use_observed=False,
)

```

Return native date values:

```python

holiday_dates = fy.holiday_dates_between(
    start=start_date,
    end=end_date,
)

```

Return ISO-formatted strings for compatibility:

```python

holiday_text = fy.holidays_between(
    start=start_date,
    end=end_date,
)

```

### Date Collections and Monthly Summaries

```python

dates = fy.fiscal_dates( )
weekdays = fy.fiscal_weekdays( )
weekends = fy.fiscal_weekends( )
workdays = fy.fiscal_workdays( )

dates_by_month = fy.dates_by_month( )
weekdays_by_month = fy.weekdays_by_month( )
weekends_by_month = fy.weekends_by_month( )
workdays_by_month = fy.workdays_by_month( )
holidays_by_month = fy.holidays_by_month( )

```

### Federal Holidays

```python

holidays = FederalHoliday( 2026 )

holiday_map = holidays.holidays( )
independence_day = holiday_map[ "Independence Day" ]

print( independence_day[ "actual" ] )
print( independence_day[ "observed" ] )

```

```python

print(
    holidays.is_holiday(
        when=date( 2026, 7, 3 ),
        observed=True,
    )
)

print( holidays.is_weekend( date( 2026, 7, 4 ) ) )

```

<a id="api-overview"></a>

![](https://github.com/is-leeroy-jenkins/fiscal/blob/master/docs/images/fiscal-classmap.png)

___

## 🧠 API Overview

```python

from fiscal import DB, Error, FederalHoliday, FiscalYear, FullTimeEquivalent, throw_if, to_date

```

### `FiscalYear`

#### Construction

```python
FiscalYear(
    fy: str | int,
    bpoa: str | int = "",
    epoa: str | int = "",
    current_date: date | datetime | str | None = None,
)
```

### Ranges and Boundaries

- `calendar_day_of_year()`
- `calendar_days_in_year()`
- `calendar_days_elapsed()`
- `calendar_days_remaining()`
- `calendar_months_elapsed()`
- `calendar_months_remaining()`
- `calendar_percent_elapsed()`
- `calendar_bounds()`
- `calendar_week_number()`
- `calendar_month_name()`
- `current_weekday_name()`
- `fiscal_day_of_year()`
- `fiscal_days_in_year()`
- `fiscal_days_elapsed()`
- `fiscal_days_remaining()`
- `fiscal_months_elapsed()`
- `fiscal_months_remaining()`
- `fiscal_percent_elapsed()`
- `fiscal_bounds()`
- `compensable_hours_elapsed(hours_per_day=8)`
- `compensable_hours_remaining(hours_per_day=8)`
- `work_hours_elapsed(hours_per_day=8, use_observed=True)`
- `work_hours_remaining(hours_per_day=8, use_observed=True)`

### Fiscal Periods

- `fiscal_month_number()`
- `fiscal_month_bounds(fiscal_month)`
- `fiscal_days_in_month(fiscal_month)`
- `fiscal_month_name(fiscal_month)`
- `fiscal_month_calendar(fiscal_month)`
- `fiscal_month_weeks(fiscal_month)`
- `fiscal_month_dates(fiscal_month)`
- `fiscal_month_day_numbers(fiscal_month)`
- `fiscal_month_text_calendar(fiscal_month)`
- `fiscal_year_text_calendar()`
- `fiscal_month_html_calendar(fiscal_month, with_year=True)`
- `fiscal_year_html_calendar(width=3)`
- `fiscal_quarter_number()`
- `fiscal_quarter_bounds(quarter)`
- `fiscal_days_in_quarter(quarter)`
- `fiscal_week_number()`
- `fiscal_week_bounds(fiscal_week)`
- `weekday_occurrences(fiscal_month, weekday)`

#### Date and Holiday Analysis

- `count_weekends(start, end)`
- `count_holidays(start, end, use_observed=True)`
- `count_workdays(start, end, use_observed=True)`
- `compensable_hours_between(start, end, hours_per_day=8)`
- `work_hours_between(start, end, hours_per_day=8, use_observed=True)`
- `fte_between(start, end, hours_per_day=8)`
- `holiday_dates_between(start, end, use_observed=True)`
- `holidays_between(start, end, use_observed=True)`
- `fiscal_dates()`
- `fiscal_weekdays()`
- `fiscal_weekends()`
- `fiscal_workdays(use_observed=True)`
- `fiscal_calendar()`
- `dates_by_month()`
- `weekdays_by_month()`
- `weekends_by_month()`
- `workdays_by_month(use_observed=True)`
- `holidays_by_month(use_observed=True)`
- `holidays_remaining(use_observed=True)`
- `workdays_remaining(use_observed=True)`
- `weekends_remaining()`
- `contains_leap_day()`
- `leap_days_in_availability()`
- `to_dict()`

### `FederalHoliday`

- `observed_date(value)`
- `holidays()`
- `is_holiday(when, observed=True)`
- `is_weekend(when)`
- `to_dict()`

### Utilities

- `throw_if(name, value)`
- `to_date(value)`
- `to_decimal(name, value)`

`to_date()` accepts `date`, `datetime`, `YYYY-MM-DD`, `MM/DD/YYYY`, and `MM/DD/YY`. Database sentinel values resolve to `None`.


### Date-Range Calendars

Render every month intersecting an inclusive date range:

```python
text_calendar = fy.date_range_text_calendar(
    start=date( 2025, 11, 15 ),
    end=date( 2026, 2, 2 ),
)
```

```python
html_calendar = fy.date_range_html_calendar(
    start=date( 2025, 11, 15 ),
    end=date( 2026, 2, 2 ),
    width=2,
    with_year=True,
)
```

The methods render November 2025 through February 2026 in chronological order. The supplied range is inclusive and constrained to the represented fiscal year.


## 📚 References

- [Fiscal Year](https://github.com/is-leeroy-jenkins/Fiscal/blob/master/resources/Definitions.md#fiscal-year)
- [Federal Holidays](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/)

<a id="license"></a>

## 📜 [License](https://github.com/is-leeroy-jenkins/fiscal/blob/master/LICENSE.txt)

MIT © 2022 Terry D. Eppler
