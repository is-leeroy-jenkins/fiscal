"""Tests for OMB full-time-equivalent calculations."""

from decimal import Decimal

import pytest

from fiscal import FullTimeEquivalent


@pytest.mark.parametrize(
	('fiscal_year', 'days', 'hours'),
	[
		(1990, 260, Decimal( '2080' )),
		(1992, 262, Decimal( '2096' )),
		(2025, 261, Decimal( '2088' )),
		(2026, 261, Decimal( '2088' )),
		(2027, 261, Decimal( '2088' )),
	],
)
def test_regular_method_denominator( fiscal_year: int, days: int, hours: Decimal ) -> None:
	"""Verify weekday counts and denominators across representative fiscal years."""
	calculator = FullTimeEquivalent( fiscal_year )

	assert calculator.compensable_days == days
	assert calculator.compensable_hours == hours


def test_regular_method_uses_fiscal_year_compensable_hours( ) -> None:
	"""Verify the regular method does not substitute the fixed 2,080-hour denominator."""
	calculator = FullTimeEquivalent( 2026 )

	assert calculator.regular_method( 2088 ) == Decimal( '1' )
	assert calculator.regular_method( 1044 ) == Decimal( '0.5' )


def test_pay_period_method_uses_fixed_denominator( ) -> None:
	"""Verify the pay-period method uses 2,080 hours even in a 2,088-hour fiscal year."""
	calculator = FullTimeEquivalent( 2026 )

	assert calculator.pay_period_method( 2080 ) == Decimal( '1' )
	assert calculator.pay_period_method( 1040 ) == Decimal( '0.5' )


def test_zero_hours_are_valid( ) -> None:
	"""Verify an organization with no qualifying hours reports zero FTEs."""
	calculator = FullTimeEquivalent( 2026 )

	assert calculator.regular_method( 0 ) == Decimal( '0' )
	assert calculator.pay_period_method( 0 ) == Decimal( '0' )


def test_inverse_hour_calculations( ) -> None:
	"""Verify planned FTE values convert to each method's required hours."""
	calculator = FullTimeEquivalent( 2026 )

	assert calculator.hours_for_regular_fte( Decimal( '1.5' ) ) == Decimal( '3132.0' )
	assert calculator.hours_for_pay_period_fte( Decimal( '1.5' ) ) == Decimal( '3120.0' )


@pytest.mark.parametrize( 'value', [-1, Decimal( '-0.01' ), float( 'nan' ), float( 'inf' )] )
def test_invalid_hour_values_are_rejected( value: object ) -> None:
	"""Verify negative and non-finite hour values cannot produce an FTE."""
	calculator = FullTimeEquivalent( 2026 )

	with pytest.raises( ValueError ):
		calculator.regular_method( value )


@pytest.mark.parametrize( 'value', [True, '2088', object( )] )
def test_nonnumeric_hour_values_are_rejected( value: object ) -> None:
	"""Verify Boolean and nonnumeric hour values raise a type error."""
	calculator = FullTimeEquivalent( 2026 )

	with pytest.raises( TypeError ):
		calculator.regular_method( value )


def test_summary_preserves_decimal_precision( ) -> None:
	"""Verify serialized calculation values are emitted as precise decimal strings."""
	calculator = FullTimeEquivalent( 2026 )
	calculator.regular_method( Decimal( '1234.5' ) )

	result = calculator.to_dict( )

	assert result[ 'method' ] == 'regular'
	assert result[ 'regular_hours' ] == '1234.5'
	assert Decimal( result[ 'fte' ] ) == Decimal( '1234.5' ) / Decimal( '2088' )
