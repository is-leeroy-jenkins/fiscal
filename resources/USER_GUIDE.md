![](https://github.com/is-leeroy-jenkins/fiscal/blob/master/docs/images/fiscal-userguide.png)

___

Fiscal provides fiscal-year, calendar-year, federal-holiday, workday, weekend, and civilian FTE calculations for use in Python applications and ad-hoc analysis.

This guide focuses on common user workflows. Database configuration, schemas, and internal query behavior are covered in the Developer Guide.

## Installation

```bash
pip install fiscal-py
```

The distribution name is `fiscal-py`; the Python import package remains `fiscal`.

## Import Fiscal

```python
from datetime import date

from fiscal import FederalHoliday, FiscalYear, FullTimeEquivalent
```

## Analyze a Fiscal Year

Create an object for the fiscal year being analyzed and supply a calculation date:

```python
fy = FiscalYear(
    fy=2026,
    current_date=date( 2026, 7, 15 ),
)
```

`current_date` controls all “current,” elapsed, remaining, month, quarter, and week calculations. When omitted, Fiscal uses the current system date.

```python
status = {
    "FiscalYear": fy.fiscal_year,
    "StartDate": fy.start_date,
    "EndDate": fy.end_date,
    "FiscalDay": fy.fiscal_day_of_year( ),
    "FiscalWeek": fy.fiscal_week_number( ),
    "FiscalMonth": fy.fiscal_month_number( ),
    "FiscalQuarter": fy.fiscal_quarter_number( ),
    "DaysElapsed": fy.fiscal_days_elapsed( ),
    "DaysRemaining": fy.fiscal_days_remaining( ),
    "PercentElapsed": round(
        fy.fiscal_percent_elapsed( ),
        2,
    ),
}

for name, value in status.items( ):
    print( f"{name}: {value}" )
```

Use integer or string fiscal-year values:

```python
fy_text = FiscalYear( "2026" )
fy_number = FiscalYear( 2026 )
```

Use BPOA and EPOA for a multi-year availability record:

```python
fy = FiscalYear(
    fy=2026,
    bpoa=2024,
    epoa=2026,
    current_date=date( 2026, 7, 15 ),
)
```

## Inspect the Stored Fiscal Record

```python
record = fy.to_dict( )

print( record[ "FiscalYear" ] )
print( record[ "BPOA" ] )
print( record[ "EPOA" ] )
print( record[ "Availability" ] )
print( record[ "Type" ] )
```

The principal fiscal-year properties are also available directly:

```python
print( fy.start_date )
print( fy.end_date )
print( fy.expiration_date )
print( fy.cancellation_date )
print( fy.weekdays )
print( fy.weekends )
print( fy.workdays )
print( fy.compensable_days )
print( fy.compensable_workdays )
print( fy.compensable_hours )
```

## Calculate Full-Time Equivalents

OMB's regular method divides fiscal-year regular straight-time hours by the compensable hours for
that fiscal year. The pay-period method divides qualifying hours from the selected 26 biweekly pay
periods by 2,080.

```python
fte = FullTimeEquivalent( 2026 )

print( fte.compensable_days )
print( fte.compensable_hours )
print( fte.regular_method( 1044 ) )
print( fte.pay_period_method( 1040 ) )
```

Include annual leave, sick leave, compensatory time off, and other approved leave in the numerator.
Exclude overtime, holiday hours worked, and terminal leave. If 27 pay periods end in the fiscal year,
omit the period with the fewest workdays in that fiscal year before passing the 26-period total.

See the MkDocs [FTE guide](../docs/user-guide/full-time-equivalents.md) for formulas, reporting
boundaries, and primary federal references.

## Analyze a Date Range

Fiscal range methods are inclusive and constrained to the represented fiscal year.

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

print( summary )
```

Observed federal holidays are used by default. Use actual dates when required:

```python
actual_holiday_count = fy.count_holidays(
    start=start_date,
    end=end_date,
    use_observed=False,
)

actual_workday_count = fy.count_workdays(
    start=start_date,
    end=end_date,
    use_observed=False,
)
```

`compensable_hours_between()` counts every Monday-through-Friday date, including holidays, for an
OMB-consistent partial-period denominator. `work_hours_between()` excludes holidays and returns
scheduled operational hours. Both default to eight hours per day, accept an alternate positive
`hours_per_day`, and return `Decimal`.

`fte_between()` divides compensable range hours by the selected fiscal year's
`CompensableHours` value and returns the annual FTE represented by that period. It does not annualize
a partial-period result.

Elapsed and remaining hours use the `current_date` supplied to `FiscalYear`:

```python
hours_status = {
    "CompensableElapsed": fy.compensable_hours_elapsed( ),
    "CompensableRemaining": fy.compensable_hours_remaining( ),
    "WorkElapsed": fy.work_hours_elapsed( ),
    "WorkRemaining": fy.work_hours_remaining( ),
}
```

Elapsed methods exclude `current_date`; remaining methods include it when it lies within the fiscal
year. Compensable methods include weekday federal holidays, while work-hour methods exclude observed
holidays by default.

A reversed range or a range that does not intersect the fiscal year raises `boogr.Error`.

## Return Holidays in a Date Range

Use `holiday_dates_between()` when an application needs native `date` values:

```python
holiday_dates = fy.holiday_dates_between(
    start=date( 2026, 1, 1 ),
    end=date( 2026, 9, 30 ),
)

for name, holiday_date in holiday_dates.items( ):
    print( f"{holiday_date}: {name}" )
```

Use `holidays_between()` when ISO-formatted string values are needed for compatibility or serialization:

```python
holiday_text = fy.holidays_between(
    start=date( 2026, 1, 1 ),
    end=date( 2026, 9, 30 ),
)
```

## Work with Fiscal Months

Federal fiscal months are numbered from October through September.

| Fiscal Month | Calendar Month |
|---:|---|
| `1` | October |
| `2` | November |
| `3` | December |
| `4` | January |
| `5` | February |
| `6` | March |
| `7` | April |
| `8` | May |
| `9` | June |
| `10` | July |
| `11` | August |
| `12` | September |

Get month boundaries and counts:

```python
fiscal_month = 10

month_start, month_end = fy.fiscal_month_bounds(
    fiscal_month,
)

month_summary = {
    "Name": fy.fiscal_month_name(
        fiscal_month,
    ),
    "StartDate": month_start,
    "EndDate": month_end,
    "CalendarDays": fy.fiscal_days_in_month(
        fiscal_month,
    ),
    "Weekdays": fy.weekdays_in_month(
        fiscal_month,
    ),
    "WeekendDays": fy.weekends_in_month(
        fiscal_month,
    ),
}

print( month_summary )
```

Count weekday occurrences by name:

```python
mondays = fy.weekday_occurrences(
    fiscal_month=10,
    weekday="Monday",
)

fridays = fy.weekday_occurrences(
    fiscal_month=10,
    weekday="Friday",
)
```

Integer weekday values from `0` through `6` remain supported for compatibility, but callers do not need to import Python’s `calendar` module.

## Render Text Calendars

Render a selected fiscal month with `calendar.TextCalendar` through Fiscal:

```python
text_month = fy.fiscal_month_text_calendar(
    fiscal_month=10,
)

print( text_month )
```

Render all twelve fiscal months in October-through-September order:

```python
text_year = fy.fiscal_year_text_calendar( )

print( text_year )
```

Consumers do not instantiate or import `TextCalendar`. Fiscal resolves the calendar year and month represented by the selected federal fiscal month.

## Render HTML Calendars

Render one fiscal month as an HTML table:

```python
html_month = fy.fiscal_month_html_calendar(
    fiscal_month=10,
    with_year=True,
)
```

Set `with_year=False` to omit the calendar year from the month heading:

```python
html_month = fy.fiscal_month_html_calendar(
    fiscal_month=10,
    with_year=False,
)
```

Render the entire fiscal year in October-through-September order:

```python
html_year = fy.fiscal_year_html_calendar(
    width=3,
)
```

`width` controls the number of month tables in each outer HTML row and accepts values from `1` through `12`.

## Work with Fiscal Quarters

```python
quarter = 4

quarter_start, quarter_end = fy.fiscal_quarter_bounds(
    quarter,
)

quarter_summary = {
    "Quarter": quarter,
    "StartDate": quarter_start,
    "EndDate": quarter_end,
    "CalendarDays": fy.fiscal_days_in_quarter(
        quarter,
    ),
    "WeekendDays": fy.count_weekends(
        quarter_start,
        quarter_end,
    ),
    "FederalHolidays": fy.count_holidays(
        quarter_start,
        quarter_end,
    ),
    "Workdays": fy.count_workdays(
        quarter_start,
        quarter_end,
    ),
}

print( quarter_summary )
```

The current quarter for `current_date` is available through:

```python
print( fy.fiscal_quarter_number( ) )
```

## Work with Fiscal Weeks

Fiscal weeks are consecutive seven-day periods beginning on the fiscal-year start date. The final week is truncated at the fiscal-year end date.

```python
fiscal_week = fy.fiscal_week_number( )

week_start, week_end = fy.fiscal_week_bounds(
    fiscal_week,
)

print( fiscal_week )
print( week_start )
print( week_end )
```

The ISO calendar-week number is separate:

```python
print( fy.calendar_week_number( ) )
```

## Build Date Collections

```python
all_dates = fy.fiscal_dates( )
weekday_dates = fy.fiscal_weekdays( )
weekend_dates = fy.fiscal_weekends( )
workday_dates = fy.fiscal_workdays( )
```

Use actual holiday dates when constructing workdays:

```python
actual_date_workdays = fy.fiscal_workdays(
    use_observed=False,
)
```

Group fiscal-year dates by month:

```python
dates_by_month = fy.dates_by_month( )

for month_name, dates in dates_by_month.items( ):
    print( month_name, len( dates ) )
```

`fiscal_calendar()` remains available as the original method. `dates_by_month()` is its clearer alias.

## Build Monthly Summaries

```python
weekdays = fy.weekdays_by_month( )
weekends = fy.weekends_by_month( )
workdays = fy.workdays_by_month( )
holidays = fy.holidays_by_month( )

monthly_summary = {
    month_name: {
        "Weekdays": weekdays[ month_name ],
        "WeekendDays": weekends[ month_name ],
        "Workdays": workdays[ month_name ],
        "FederalHolidays": holidays[ month_name ],
    }
    for month_name in weekdays
}

print( monthly_summary )
```

## Determine Remaining Fiscal-Year Time

```python
remaining = {
    "CalendarDays": fy.fiscal_days_remaining( ),
    "Workdays": fy.workdays_remaining( ),
    "WeekendDays": fy.weekends_remaining( ),
    "FederalHolidays": fy.holidays_remaining( ),
}

print( remaining )
```

For a future fiscal year, remaining calculations begin at the fiscal-year start date. For a completed fiscal year, they return zero.

## Inspect Federal Holidays

```python
holidays = FederalHoliday( 2026 )
holiday_map = holidays.holidays( )

for name, values in holiday_map.items( ):
    print(
        name,
        values[ "actual" ],
        values[ "observed" ],
    )
```

Check a date:

```python
print(
    holidays.is_holiday(
        when=date( 2026, 7, 3 ),
        observed=True,
    )
)

print(
    holidays.is_holiday(
        when=date( 2026, 7, 4 ),
        observed=False,
    )
)

print(
    holidays.is_weekend(
        date( 2026, 7, 4 ),
    )
)
```

Calculate an observed date:

```python
print(
    holidays.observed_date(
        date( 2026, 7, 4 ),
    )
)
```

The observed-date rules are:

- Saturday: preceding Friday
- Sunday: following Monday
- Monday through Friday: unchanged

## Detect Leap Days

```python
print( fy.contains_leap_day( ) )
print( fy.leap_days_in_availability( ) )
```

`contains_leap_day()` evaluates the represented fiscal year. `leap_days_in_availability()` evaluates the inclusive start and end dates stored for the selected availability record.

## Use Fiscal with pandas

```python
import pandas as pd

df_fiscal_year = pd.DataFrame(
    [ fy.to_dict( ) ]
)

df_holidays = pd.DataFrame(
    [
        {
            "Holiday": name,
            "Date": holiday_date,
        }
        for name, holiday_date
        in fy.holiday_dates_between(
            start=fy.start_date,
            end=fy.end_date,
        ).items( )
    ]
)

df_months = pd.DataFrame(
    [
        {
            "Month": month_name,
            "Weekdays": fy.weekdays_by_month( )[ month_name ],
            "WeekendDays": fy.weekends_by_month( )[ month_name ],
            "Workdays": fy.workdays_by_month( )[ month_name ],
            "FederalHolidays": len(
                fy.holidays_by_month( )[ month_name ],
            ),
        }
        for month_name in fy.dates_by_month( )
    ]
)
```

Export results:

```python
df_months.to_csv(
    "fiscal-month-summary.csv",
    index=False,
)
```

## Boundary Checks

```python
print( fy.is_fiscal_start_year( ) )
print( fy.is_fiscal_end_year( ) )
print( fy.is_calendar_start_year( ) )
print( fy.is_calendar_end_date( ) )
```

These methods compare `current_date` to the exact boundary date.

## Calendar Matrices

Return complete Monday-through-Sunday date rows:

```python
date_rows = fy.fiscal_month_dates(
    fiscal_month=10,
)
```

Return day-number rows with zero placeholders for adjacent months:

```python
day_number_rows = fy.fiscal_month_day_numbers(
    fiscal_month=10,
)
```

The original method names remain available:

```python
date_rows = fy.fiscal_month_calendar( 10 )
day_number_rows = fy.fiscal_month_weeks( 10 )
```

## Input Errors

Fiscal wraps operational failures in `boogr.Error`. Typical causes include:

- an unavailable fiscal-year record
- an invalid fiscal month, quarter, week, or weekday
- a reversed date range
- a range that does not intersect the represented fiscal year
- missing database tables or columns
- malformed database values


## Generate Calendars for a Date Range

Use `date_range_text_calendar()` to render every calendar month intersecting an inclusive range:

```python
text_calendar = fy.date_range_text_calendar(
    start=date( 2025, 11, 15 ),
    end=date( 2026, 2, 2 ),
)

print( text_calendar )
```

Generate equivalent HTML:

```python
html_calendar = fy.date_range_html_calendar(
    start=date( 2025, 11, 15 ),
    end=date( 2026, 2, 2 ),
    width=2,
    with_year=True,
)
```

The first and final months are rendered as complete month calendars. The range is inclusive and constrained to the represented fiscal year. Reversed ranges and ranges that do not intersect the represented fiscal year raise `boogr.Error`.
