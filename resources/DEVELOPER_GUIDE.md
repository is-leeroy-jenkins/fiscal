# Fiscal Developer Guide

Fiscal is a SQLite-backed Python package for federal fiscal-year, calendar-year, federal-holiday, workday, weekend, and civilian FTE calculations.

This guide documents the audited implementation in `fiscal/__init__.py`.

## Public Package Contract

```python
from fiscal import DB, Error, FederalHoliday, FiscalYear, FullTimeEquivalent, throw_if, to_date, to_decimal, weekday_number
```

The audited `__all__` contract exports:

```python
__all__: tuple[ str, ... ] = (
    "DB",
    "Error",
    "FederalHoliday",
    "FiscalYear",
    "FullTimeEquivalent",
    "throw_if",
    "to_date",
    "to_decimal",
    "weekday_number",
)
```

Shared public validation and date-normalization helpers are implemented in `fiscal/utilities.py`.

## Runtime Dependencies

Standard-library dependencies:

```text
calendar
sqlite3
datetime
typing
```

Third-party runtime dependency:

```text
pandas
```

Install external runtime dependencies with:

```bash
pip install -e .
```

## Configuration Contract

`fiscal/config.py` supplies package-relative defaults for:

```python
DB_PATH: str
LOG_PATH: Path

TABLES: list[ str ] = [
    "BudgetFiscalYears",
    "FederalHolidays",
]
```

Applications may override `DB_PATH`, `LOG_PATH`, and the documented logging switches with environment
variables. The implementation uses positional table selection:

| Index | Consumer |
|---:|---|
| `0` | `FiscalYear` |
| `1` | `FederalHoliday` and `FiscalYear.holidays` |

Changing the order changes runtime behavior.

## Database Contract

### `BudgetFiscalYears`

A fiscal-year query uses:

```sql
SELECT *
FROM "BudgetFiscalYears"
WHERE FiscalYear = ?
  AND BPOA = ?
  AND EPOA = ?;
```

Exactly one row must be returned.

Required columns:

| Column | Conversion |
|---|---|
| `ID` | `int` |
| `FiscalYear` | `str` |
| `BPOA` | `str` |
| `EPOA` | `str` |
| `StartDate` | `to_date()` |
| `EndDate` | `to_date()` |
| `ExpirationDate` | `to_date()` |
| `CancellationDate` | `to_date()` |
| `Weekdays` | `int` |
| `Weekends` | `int` |
| `Workdays` | `float` |
| `CompensableDays` | `float` |
| `CompensableHours` | `float` |
| `Type` | `str` |
| `Availability` | `str` |

`compensable_workdays` is initialized as a backward-compatible alias for `compensable_days`.

### `FederalHolidays`

A holiday query uses:

```sql
SELECT *
FROM "FederalHolidays"
WHERE FiscalYear = ?;
```

Exactly one row must be returned.

Required columns:

| Column | Domain member |
|---|---|
| `ID` | `id` |
| `FiscalYear` | `fiscal_year` |
| `ColumbusDay` | `columbus_day` |
| `VeteransDay` | `veterans_day` |
| `ThanksgivingDay` | `thanksgiving_day` |
| `ChristmasDay` | `christmas_day` |
| `NewYearsDay` | `new_years_day` |
| `MartinLutherKingDay` | `martin_luther_king_day` |
| `PresidentsDay` | `presidents_day` |
| `MemorialDay` | `memorial_day` |
| `JuneteenthDay` | `juneteenth_day` |
| `IndependenceDay` | `independence_day` |
| `LaborDay` | `labor_day` |

## Input Utilities

### `throw_if()`

```python
throw_if(
    name: str,
    value: object,
) -> None
```

The guard rejects:

- `None`
- blank strings
- empty lists, tuples, dictionaries, and sets

It does not reject valid numeric zero.

### `to_date()`

```python
to_date(
    value: date | datetime | str | None,
) -> date | None
```

Supported text formats:

```text
YYYY-MM-DD
MM/DD/YYYY
MM/DD/YY
```

These database sentinel values resolve to `None`:

```text
""
NS
N/A
NA
NONE
NULL
```

Unsupported text raises `ValueError`. Unsupported types raise `TypeError`.

### `_weekday_number()`

```python
_weekday_number(
    value: int | str,
) -> int
```

Accepted names are full English weekday names, case-insensitively:

```text
Monday
Tuesday
Wednesday
Thursday
Friday
Saturday
Sunday
```

Integers from `0` through `6` remain supported for compatibility.

## Database Access

### `DB.create_connection()`

Uses `sqlite3.connect(cfg.DB_PATH)`.

### `DB.query_year()`

- validates all arguments
- validates the table against `cfg.TABLES`
- uses parameterized SQL
- requires exactly one result row
- returns a copied `pandas.DataFrame`

### `DB.query_holiday()`

- validates the table and fiscal year
- uses parameterized SQL
- requires exactly one result row
- returns a copied `pandas.DataFrame`

Failures are wrapped as `boogr.Error` with module, cause, and method metadata.

## `FiscalYear` Construction

```python
FiscalYear(
    fy: str | int,
    bpoa: str | int = "",
    epoa: str | int = "",
    current_date: date | datetime | str | None = None,
)
```

Construction performs these steps:

1. Initialize database configuration.
2. Validate `fy`.
3. Normalize fiscal-year, BPOA, and EPOA values to strings.
4. Query exactly one `BudgetFiscalYears` row.
5. Convert and assign database fields.
6. Initialize `compensable_workdays`.
7. Normalize the calculation date.
8. Derive the calendar year and calendar boundaries.

When `current_date` is omitted, the system date is used. Tests and reproducible analysis should supply it explicitly.

## Calculation-Date Semantics

The following methods depend on `current_date`:

- calendar and fiscal elapsed/remaining calculations
- calendar and fiscal percentages
- current fiscal month, quarter, and week
- current calendar week
- current weekday and month names
- remaining holiday, workday, and weekend counts
- fiscal and calendar boundary predicates

The fiscal-year database record and the calculation date are independent. A date before, within, or after the represented fiscal year is valid.

## Fiscal Range Contract

`_fiscal_range()` is the common range-validation path used by:

- `count_weekends()`
- `count_holidays()`
- `count_workdays()`
- `compensable_hours_between()`
- `work_hours_between()`
- `holiday_dates_between()`
- `holidays_between()`

It:

1. validates both arguments
2. converts them with `to_date()`
3. rejects reversed ranges
4. clamps the range to the represented fiscal year
5. rejects ranges with no fiscal-year intersection

All public range methods are inclusive.

## Calendar and Fiscal Progress

Calendar methods operate on the calendar year containing `current_date`.

Fiscal methods operate relative to the selected fiscal-year record.

Exact-boundary predicates are:

```python
is_fiscal_start_year()
is_fiscal_end_year()
is_calendar_start_year()
is_calendar_end_date()
```

Each compares `current_date` to the exact boundary date.

## Fiscal Months

Federal fiscal-month numbering is:

```text
1  October
2  November
3  December
4  January
5  February
6  March
7  April
8  May
9  June
10 July
11 August
12 September
```

Core methods:

```python
fiscal_month_number()
fiscal_month_bounds(fiscal_month)
fiscal_days_in_month(fiscal_month)
fiscal_month_name(fiscal_month)
weekdays_in_month(fiscal_month)
weekends_in_month(fiscal_month)
weekday_occurrences(fiscal_month, weekday)
```

`weekday_occurrences()` accepts names and legacy integer values.

## Calendar Matrices and Compatibility Aliases

Original methods:

```python
fiscal_month_calendar(
    fiscal_month: int,
) -> list[ list[ date ] ]

fiscal_month_weeks(
    fiscal_month: int,
) -> list[ list[ int ] ]
```

Clearer aliases:

```python
fiscal_month_dates(
    fiscal_month: int,
) -> list[ list[ date ] ]

fiscal_month_day_numbers(
    fiscal_month: int,
) -> list[ list[ int ] ]
```

The date matrix retains adjacent-month dates to produce complete Monday-through-Sunday rows. The integer matrix uses zero placeholders for adjacent months.

## Text and HTML Calendar Rendering

The rendering functionality is integrated directly into `FiscalYear`. No additional classes are introduced.

```python
fiscal_month_text_calendar(
    fiscal_month: int,
) -> str

fiscal_year_text_calendar( ) -> str

fiscal_month_html_calendar(
    fiscal_month: int,
    with_year: bool = True,
) -> str

fiscal_year_html_calendar(
    width: int = 3,
) -> str
```

Implementation behavior:

- `fiscal_month_text_calendar()` uses `calendar.TextCalendar` with Monday as the first weekday.
- `fiscal_year_text_calendar()` joins twelve fiscal-month renderings in October-through-September order.
- `fiscal_month_html_calendar()` uses `calendar.HTMLCalendar` with Monday as the first weekday.
- `fiscal_year_html_calendar()` groups twelve HTML month tables into rows controlled by `width`.
- `width` must be an integer from `1` through `12`; boolean values are rejected.
- All rendering failures are wrapped in `boogr.Error`.
- The four methods are included in `FiscalYear.__dir__()`.

The fiscal-year methods deliberately do not call `TextCalendar.formatyear()` or `HTMLCalendar.formatyear()` because those APIs render January through December. Fiscal must preserve October-through-September ordering across two calendar years.

## Fiscal Quarters

```python
fiscal_quarter_number() -> int
fiscal_quarter_bounds(quarter: int) -> tuple[date, date]
fiscal_days_in_quarter(quarter: int) -> int
```

Quarter values are restricted to `1` through `4`.

## Fiscal Weeks

```python
fiscal_week_number() -> int
fiscal_week_bounds(fiscal_week: int) -> tuple[date, date]
```

Fiscal weeks are consecutive seven-day periods beginning on `start_date`. The final week is truncated at `end_date`.

This definition is distinct from ISO calendar weeks returned by `calendar_week_number()`.

## Date Collections

```python
fiscal_dates() -> list[date]
fiscal_weekdays() -> list[date]
fiscal_weekends() -> list[date]
fiscal_workdays(use_observed=True) -> list[date]
```

`fiscal_weekdays()` includes Monday through Friday without removing holidays.

`fiscal_workdays()` removes either observed or actual federal holidays.

## Month Grouping

Original method:

```python
fiscal_calendar() -> dict[str, list[date]]
```

Clearer alias:

```python
dates_by_month() -> dict[str, list[date]]
```

Summary methods:

```python
weekdays_by_month() -> dict[str, int]
weekends_by_month() -> dict[str, int]
workdays_by_month(use_observed=True) -> dict[str, int]
holidays_by_month(use_observed=True) -> dict[str, list[date]]
```

All twelve fiscal months are included.

## Holiday Contracts

### `FiscalYear.holidays`

This property preserves the database-oriented compatibility contract:

```python
list[dict[str, str]]
```

It excludes `ID` and `FiscalYear`, converts nulls to empty strings, and retains the database column names.

### `FederalHoliday.holidays()`

Returns domain holiday names with native actual and observed dates:

```python
dict[str, dict[str, date]]
```

### `FiscalYear.holiday_dates_between()`

Preferred application contract:

```python
dict[str, date]
```

### `FiscalYear.holidays_between()`

Compatibility contract:

```python
dict[str, str]
```

The string values are ISO-formatted dates.

## Remaining-Time Methods

```python
holidays_remaining(use_observed=True) -> int
workdays_remaining(use_observed=True) -> int
weekends_remaining() -> int
```

Behavior:

- completed fiscal year: `0`
- current fiscal year: count from `current_date`
- future fiscal year: count from `start_date`

Counts are inclusive.

## Leap-Day Methods

```python
contains_leap_day() -> bool
leap_days_in_availability() -> int
```

`contains_leap_day()` checks the represented fiscal-year boundaries.

`leap_days_in_availability()` checks the stored inclusive start and end dates for the selected fiscal-year/BPOA/EPOA record.

## `FederalHoliday`

```python
FederalHoliday(
    fiscal_year: str | int,
)
```

The class loads one database row and exposes the stored holidays as date-valued members.

### Observed dates

```python
observed_date(value: date) -> date
```

Rules:

- Saturday: preceding Friday
- Sunday: following Monday
- weekday: unchanged

### Membership tests

```python
is_holiday(
    when: date | datetime,
    observed: bool = True,
) -> bool

is_weekend(
    when: date | datetime,
) -> bool
```

### Dictionary export

```python
to_dict() -> dict[str, object]
```

The export retains database-oriented field names and includes `ID` and `FiscalYear`.

## Error Handling

Operational methods use this pattern:

```python
except Exception as e:
    ex = Error( e )
    ex.module = "fiscal"
    ex.cause = "FiscalYear"
    ex.method = "method_signature"
    raise ex
```

Database and holiday methods use their corresponding causes.

Callers should catch `boogr.Error` when handling operational failures.

## Audited Runtime Coverage

The audited module was exercised through:

- compilation and import
- all exported utilities
- every constructor
- every property and public method
- all compatibility aliases
- all twelve text and HTML fiscal-month renderings
- fiscal-year text rendering
- fiscal-year HTML widths `1`, `2`, `3`, `4`, `6`, and `12`
- invalid text/HTML month values and invalid HTML widths
- fiscal months `1` through `12`
- fiscal quarters `1` through `4`
- valid and invalid fiscal weeks
- weekday names and integer values
- leap and non-leap fiscal years
- actual and observed holiday branches
- fiscal and calendar boundary dates
- past, current, and future fiscal-year calculations
- reversed and nonintersecting ranges
- missing records and unsupported tables

The automated pytest suite validates package installation, database integration, date normalization,
diagnostic sanitization, and both OMB FTE methods.

## Extension Guidelines

When adding functionality:

1. Preserve existing public members and compatibility aliases.
2. Accept domain-friendly inputs rather than exposing standard-library constants.
3. Use `current_date` for reproducible date-dependent calculations.
4. Route fiscal range operations through `_fiscal_range()`.
5. Return native `date` values in new domain APIs.
6. Preserve string-returning methods only where compatibility requires them.
7. Use `throw_if()` for required arguments.
8. Wrap operational exceptions in `boogr.Error`.
9. Keep DataFrame variables prefixed with `df_`.
10. Update `__dir__()`, README, User Guide, Developer Guide, and runtime tests together.

## Validation Checklist

Before release:

```bash
python -m compileall -q fiscal
python -m pytest
python -m mkdocs build --strict
```

Confirm:

- `fiscal/config.py` exposes `DB_PATH` and ordered `TABLES`
- both SQLite tables exist
- all required columns exist
- each query returns exactly one row
- date fields use supported formats or sentinels
- every public method has a valid execution-path test
- actual and observed holiday branches are covered
- fiscal start, end, leap-day, and final-week boundaries are covered


## Date-Range Calendar Rendering

The range renderers are implemented directly on `FiscalYear` and add no classes:

```python
date_range_text_calendar(
    start: date | datetime,
    end: date | datetime,
) -> str

date_range_html_calendar(
    start: date | datetime,
    end: date | datetime,
    width: int = 3,
    with_year: bool = True,
) -> str
```

Both methods route dates through `_fiscal_range()`, reject reversed or nonintersecting ranges, clamp intersecting ranges to the represented fiscal year, and render each intersecting month chronologically. The boundary months remain complete month calendars.
