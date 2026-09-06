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

## Boundary Checks

```python
print( fy.is_fiscal_start_year( ) )
print( fy.is_fiscal_end_year( ) )
print( fy.is_calendar_start_year( ) )
print( fy.is_calendar_end_date( ) )
```

Each predicate compares the current date with the exact corresponding boundary date.
