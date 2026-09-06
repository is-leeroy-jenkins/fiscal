# Date Ranges

Fiscal range methods are inclusive and constrained to the represented fiscal year.

## Count Days

```python
from datetime import date

start_date = date( 2026, 7, 1 )
end_date = date( 2026, 7, 31 )

weekends = fy.count_weekends( start_date, end_date )
holidays = fy.count_holidays( start_date, end_date )
workdays = fy.count_workdays( start_date, end_date )
```

## Calculate Hours

Calculate OMB compensable hours by counting every Monday-through-Friday date, including federal
holidays:

```python
compensable_hours = fy.compensable_hours_between(
    start=start_date,
    end=end_date,
)
```

Calculate scheduled federal work hours after excluding observed holidays:

```python
work_hours = fy.work_hours_between(
    start=start_date,
    end=end_date,
)
```

Both methods default to eight hours per day and return `Decimal`. Supply a different positive daily
schedule when needed:

```python
part_time_work_hours = fy.work_hours_between(
    start=start_date,
    end=end_date,
    hours_per_day=6,
)
```

## Return Holiday Dates

Preferred native-date contract:

```python
holiday_dates = fy.holiday_dates_between(
    start=start_date,
    end=end_date,
)
```

Compatibility ISO-string contract:

```python
holiday_text = fy.holidays_between(
    start=start_date,
    end=end_date,
)
```

A reversed range or a range that does not intersect the represented fiscal year raises `boogr.Error`.
