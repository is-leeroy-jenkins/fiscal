"""Integration tests for Fiscal's packaged database and public helpers."""

import sqlite3
from datetime import date, datetime

import pytest

from fiscal import FiscalYear, FullTimeEquivalent, throw_if, to_date, weekday_number
from fiscal import config


def test_packaged_database_exists_and_opens( ) -> None:
	"""Verify the installed-package database path resolves to a usable SQLite file."""
	assert config.DB_PATH.endswith( 'fiscal/sqlite/data.db' )
	with sqlite3.connect( config.DB_PATH ) as connection:
		count = connection.execute( 'SELECT COUNT(*) FROM BudgetFiscalYears' ).fetchone( )[ 0 ]
	assert count > 0


def test_database_denominators_match_calculated_weekdays( ) -> None:
	"""Cross-check all annual database rows against the OMB regular-method denominator."""
	with sqlite3.connect( config.DB_PATH ) as connection:
		rows = connection.execute(
			'''SELECT FiscalYear, CompensableDays, CompensableHours
			FROM BudgetFiscalYears
			WHERE FiscalYear = BPOA AND FiscalYear = EPOA'''
		).fetchall( )

	for fiscal_year, database_days, database_hours in rows:
		calculator = FullTimeEquivalent( int( fiscal_year ) )
		assert calculator.compensable_days == int( database_days )
		assert calculator.compensable_hours == int( database_hours )


def test_fiscal_year_accepts_reproducible_current_date( ) -> None:
	"""Verify explicit calculation dates replace dependency on the system clock."""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.current_date == date( 2026, 7, 15 )
	assert fiscal_year.calendar_year == 2026
	assert fiscal_year.fiscal_month_number( ) == 10
	assert fiscal_year.fiscal_quarter_number( ) == 4


@pytest.mark.parametrize(
	('value', 'expected'),
	[
		(date( 2026, 7, 15 ), date( 2026, 7, 15 )),
		(datetime( 2026, 7, 15, 12, 30 ), date( 2026, 7, 15 )),
		('2026-07-15', date( 2026, 7, 15 )),
		('07/15/2026', date( 2026, 7, 15 )),
	],
)
def test_to_date_supported_values( value: object, expected: date ) -> None:
	"""Verify public date normalization accepts every documented representation."""
	assert to_date( value ) == expected


def test_public_argument_guard_allows_zero( ) -> None:
	"""Verify the required-value guard does not reject meaningful numeric zero."""
	assert throw_if( 'value', 0 ) is None
	with pytest.raises( ValueError ):
		throw_if( 'value', '' )


def test_weekday_names_and_numbers( ) -> None:
	"""Verify weekday normalization supports names and Python weekday numbers."""
	assert weekday_number( 'Monday' ) == 0
	assert weekday_number( 6 ) == 6
	with pytest.raises( ValueError ):
		weekday_number( 'Funday' )
