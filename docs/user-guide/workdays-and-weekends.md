# Workdays and Weekends

## Fiscal-Year Collections

```python
all_dates = fy.fiscal_dates( )
weekday_dates = fy.fiscal_weekdays( )
weekend_dates = fy.fiscal_weekends( )
workday_dates = fy.fiscal_workdays( )
```

Observed holidays are excluded from workdays by default.

```python
actual_date_workdays = fy.fiscal_workdays(
    use_observed=False,
)
```

## Date-Range Hours

```python
compensable_hours = fy.compensable_hours_between(
    start=start_date,
    end=end_date,
)

work_hours = fy.work_hours_between(
    start=start_date,
    end=end_date,
)
```

Compensable hours include all Monday-through-Friday dates, including holidays. Work hours exclude
observed holidays by default. Pass `use_observed=False` to `work_hours_between()` to exclude statutory
holiday dates instead.

## Monthly Counts

```python
weekdays = fy.weekdays_by_month( )
weekends = fy.weekends_by_month( )
workdays = fy.workdays_by_month( )
holidays = fy.holidays_by_month( )
```

## Remaining Counts

```python
remaining = {
    "Holidays": fy.holidays_remaining( ),
    "Workdays": fy.workdays_remaining( ),
    "WeekendDays": fy.weekends_remaining( ),
}
```
