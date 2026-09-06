"""Integration tests for Fiscal's packaged database and public API.

Purpose:
	Verifies database packaging, fiscal-period calculations, date-range behavior, compensable and
	holiday-adjusted work hours, annual range FTEs, progress boundaries, and shared input utilities.
	The tests exercise installed-package contracts through public imports from ``fiscal``.
"""

import sqlite3
from datetime import date, datetime
from decimal import Decimal

import pytest

from fiscal import (Error, FiscalYear, FullTimeEquivalent, throw_if, to_date, to_decimal,
	weekday_number)
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


def test_compensable_hours_between_includes_weekday_holidays( ) -> None:
	"""Verify the OMB partial-range denominator retains weekday federal holidays."""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.compensable_hours_between(
		'2026-07-01', '2026-07-31' ) == Decimal( '184' )
	assert fiscal_year.compensable_hours_between(
		fiscal_year.start_date, fiscal_year.end_date ) == Decimal( '2088' )


def test_work_hours_between_excludes_observed_holidays( ) -> None:
	"""Verify operational work hours distinguish observed and statutory holiday dates."""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.work_hours_between(
		'2026-07-03', '2026-07-04' ) == Decimal( '0' )
	assert fiscal_year.work_hours_between(
		'2026-07-03', '2026-07-04', use_observed=False ) == Decimal( '8' )


def test_range_hours_support_alternate_daily_schedules( ) -> None:
	"""Verify date-range hours preserve fractional daily schedules exactly."""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.work_hours_between(
		'2026-07-01', '2026-07-31', hours_per_day=7.5 ) == Decimal( '165.0' )


@pytest.mark.parametrize( 'value', [0, -1, True, '8', float( 'nan' )] )
def test_range_hours_reject_invalid_daily_hours( value: object ) -> None:
	"""Verify empty, invalid, and nonpositive daily-hour values cannot produce results."""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	with pytest.raises( Error ):
		fiscal_year.compensable_hours_between(
			'2026-07-01', '2026-07-31', hours_per_day=value )


def test_to_decimal_preserves_numeric_text_representation( ) -> None:
	"""Verify shared numeric conversion avoids binary floating-point expansion."""
	assert to_decimal( 'hours', 7.5 ) == Decimal( '7.5' )


def test_fte_between_returns_annual_budgetary_fraction( ) -> None:
	"""Verify range FTE uses the represented fiscal year's compensable-hour denominator.

	Purpose:
		Confirms that a full-time full-year schedule returns one FTE, a six-hour full-year schedule
		returns 0.75 FTE, and a partial range returns its exact annual FTE fraction.

	Returns:
		None: Assertions report calculation-contract failures.
	"""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.fte_between(
		fiscal_year.start_date, fiscal_year.end_date ) == Decimal( '1' )
	assert fiscal_year.fte_between(
		fiscal_year.start_date, fiscal_year.end_date,
		hours_per_day=6 ) == Decimal( '0.75' )
	assert fiscal_year.fte_between(
		'2026-07-01', '2026-07-31' ) == Decimal( '184' ) / Decimal( '2088' )


def test_elapsed_and_remaining_compensable_hours( ) -> None:
	"""Verify compensable-hour progress partitions the fiscal year at the calculation date.

	Purpose:
		Confirms elapsed hours stop before the calculation date, remaining hours begin on that date,
		and both values sum to the complete fiscal-year compensable-hour denominator.

	Returns:
		None: Assertions report hour-progress calculation failures.
	"""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.compensable_hours_elapsed( ) == Decimal( '1640' )
	assert fiscal_year.compensable_hours_remaining( ) == Decimal( '448' )
	assert (fiscal_year.compensable_hours_elapsed( )
		+ fiscal_year.compensable_hours_remaining( )) == Decimal( '2088' )


def test_elapsed_and_remaining_work_hours( ) -> None:
	"""Verify work-hour progress excludes observed federal holidays.

	Purpose:
		Confirms elapsed and remaining operational work-hour calculations apply the default observed
		holiday calendar on both sides of the calculation date.

	Returns:
		None: Assertions report holiday-adjusted hour calculation failures.
	"""
	fiscal_year = FiscalYear( 2026, current_date='2026-07-15' )

	assert fiscal_year.work_hours_elapsed( ) == Decimal( '1560' )
	assert fiscal_year.work_hours_remaining( ) == Decimal( '440' )


def test_hour_progress_handles_dates_outside_fiscal_year( ) -> None:
	"""Verify hour progress remains bounded outside the represented fiscal year.

	Purpose:
		Confirms a future fiscal year has zero elapsed and all remaining compensable hours, while a
		completed fiscal year has all elapsed and zero remaining compensable hours.

	Returns:
		None: Assertions report fiscal-boundary handling failures.
	"""
	future = FiscalYear( 2026, current_date='2025-09-30' )
	completed = FiscalYear( 2026, current_date='2026-10-01' )

	assert future.compensable_hours_elapsed( ) == Decimal( '0' )
	assert future.compensable_hours_remaining( ) == Decimal( '2088' )
	assert completed.compensable_hours_elapsed( ) == Decimal( '2088' )
	assert completed.compensable_hours_remaining( ) == Decimal( '0' )


@pytest.mark.parametrize( 'method_name', [
	'compensable_hours_elapsed',
	'compensable_hours_remaining',
	'work_hours_elapsed',
	'work_hours_remaining',
] )
def test_hour_progress_validates_daily_hours_before_boundary_return(
	method_name: str ) -> None:
	"""Verify boundary short-circuits do not bypass daily-schedule validation.

	Purpose:
		Invokes each hour-progress method outside the fiscal-year range to confirm it validates the
		daily schedule before returning a boundary result.

	Args:
		method_name (str): Public hour-progress method selected by the parameterized test.

	Returns:
		None: The expected exception assertion reports validation failures.
	"""
	fiscal_year = FiscalYear( 2026, current_date='2025-09-30' )
	method = getattr( fiscal_year, method_name )

	with pytest.raises( Error ):
		method( hours_per_day=0 )
