# Calendar and Fiscal Progress

Fiscal uses `datetime.today().date()` to initialize the current calculation date unless the caller
provides an explicit date. Use an explicit date for tests, reports, and reproducible analysis:

```python
from fiscal import FiscalYear

fy = FiscalYear( 2026, current_date="2026-07-15" )
```

## Calendar Progress

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
```

## Fiscal Progress

```python
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
}
```

## Fiscal Hour Progress

```python
hour_status = {
    "CompensableHoursElapsed": fy.compensable_hours_elapsed( ),
    "CompensableHoursRemaining": fy.compensable_hours_remaining( ),
    "WorkHoursElapsed": fy.work_hours_elapsed( ),
    "WorkHoursRemaining": fy.work_hours_remaining( ),
}
```

Elapsed-hour methods count through the day before `current_date`. Remaining-hour methods count from
`current_date` through fiscal-year end, including the current date when it is inside the fiscal
year. Compensable hours include weekday federal holidays; work hours exclude observed holidays by
default. All four methods accept a positive `hours_per_day` and return `Decimal`.

## Boundary Checks

```python
print( fy.is_fiscal_start_year( ) )
print( fy.is_fiscal_end_year( ) )
print( fy.is_calendar_start_year( ) )
print( fy.is_calendar_end_date( ) )
```

Each predicate compares the current date with the exact corresponding boundary date.
