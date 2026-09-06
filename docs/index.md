# Fiscal
![fiscal](images/project-fiscal.png)
___

Fiscal provides U.S. federal fiscal-year, calendar-year, federal-holiday, workday, FTE, weekend, and calendar-rendering tools for Python.

The package combines SQLite-backed fiscal records with date calculations for fiscal months, quarters, weeks, holidays, and inclusive date ranges.

## Purpose

Fiscal supports applications that need to:

- load authoritative fiscal-year and federal-holiday records
- calculate calendar-year and fiscal-year progress
- resolve fiscal-month, fiscal-quarter, and fiscal-week boundaries
- count weekdays, weekends, workdays, and holidays
- calculate civilian FTEs using either OMB method
- generate text and HTML calendars
- render calendars for fiscal months, fiscal years, and date ranges
- export fiscal-year and federal-holiday records as dictionaries

## Installation

```bash
pip install fiscal
```

## Quick Start

```python
from datetime import date

from fiscal import FederalHoliday, FiscalYear, FullTimeEquivalent

fy = FiscalYear(
    fy=2026,
)

print( fy.fiscal_month_number( ) )
print( fy.fiscal_quarter_number( ) )
print( fy.fiscal_week_number( ) )

workdays = fy.count_workdays(
    start=date( 2026, 7, 1 ),
    end=date( 2026, 7, 31 ),
)

print( workdays )

fte = FullTimeEquivalent( 2026 )
print( fte.regular_method( 1044 ) )
```

Fiscal initializes `current_date` with `datetime.today().date()` unless the constructor receives an
explicit reproducible calculation date.

## Documentation

- [Architecture](architecture.md)
- [User Guide](user-guide/index.md)
- [API Reference](api/index.md)
- [Development](development.md)

## License

Fiscal is distributed under the MIT License.

Copyright © 2022 Terry D. Eppler
