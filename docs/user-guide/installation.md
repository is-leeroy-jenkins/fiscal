# Installation

## Install the Package

```bash
pip install fiscal-pi
```

The distribution name avoids a collision with the unrelated `fiscal` project already registered on
PyPI. The installed import package remains `fiscal`:

```python
import fiscal
```

Install the project and its development dependencies from a source checkout:

```bash
pip install -e ".[dev]"
```

## Configure the Database

Fiscal ships with the SQLite reference data and default configuration. Applications may override the
data and logging paths with environment variables:

```bash
DB_PATH=/path/to/fiscal.db
LOG_PATH=/path/to/Exceptions.db
```

An overridden database must retain the `BudgetFiscalYears` and `FederalHolidays` schemas expected by
the package.

## Verify the Installation

```python
from fiscal import FiscalYear

fy = FiscalYear( 2026 )
print( fy.fiscal_year )
```

A missing database, table, record, or required column raises Fiscal's bundled `Error` wrapper.
