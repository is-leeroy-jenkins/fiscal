"""Federal civilian full-time-equivalent calculations.

The calculations in this module implement the regular and pay-period methods
defined by section 85 of OMB Circular No. A-11. They measure budgetary FTEs,
which are based on regular straight-time hours and are distinct from employee
headcounts and workload-planning estimates of available workhours.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict

from .utilities import throw_if, to_decimal


class FullTimeEquivalent( ):
	"""Calculate federal civilian full-time equivalents under OMB methods.

	Purpose:
		Computes budgetary FTEs from regular straight-time hours using either the
		regular method or the pay-period method described in OMB Circular No. A-11,
		section 85. The class also derives the regular-method denominator for the
		selected federal fiscal year.

		Input hours should include annual leave, sick leave, compensatory time off,
		and other approved leave. They should exclude overtime, holiday hours worked,
		and terminal leave. The class performs arithmetic only; callers remain
		responsible for classifying source hours correctly.

	Attributes:
		fiscal_year (int): Ending calendar year of the federal fiscal year.
		start_date (date): October 1 start of the fiscal year.
		end_date (date): September 30 end of the fiscal year.
		hours_per_day (Decimal): Regular-method hours assigned to each weekday.
		compensable_days (int): Monday-through-Friday days in the fiscal year.
		compensable_hours (Decimal): Regular-method FTE denominator.
		method (str): Method used by the most recent calculation.
		regular_hours (Decimal): Numerator used by the most recent calculation.
		fte (Decimal): Result of the most recent calculation without forced rounding.

	Note:
		This class applies to civilian FTE reporting. OMB instructs agencies to report
		active-duty military personnel using average strength instead of FTEs.
	"""

	PAY_PERIOD_COMPENSABLE_HOURS: Decimal = Decimal( '2080' )

	def __init__( self, fiscal_year: int, hours_per_day: int | float | Decimal = 8 ) -> None:
		"""Initialize an FTE calculator for a federal fiscal year.

		Purpose:
			Builds the fiscal-year date range and computes its regular-method
			compensable days and hours. Federal fiscal year 2026, for example, runs
			from October 1, 2025 through September 30, 2026.

		Args:
			fiscal_year (int): Four-digit ending year of the federal fiscal year.
			hours_per_day (int | float | Decimal): Straight-time hours assigned to
				each Monday-through-Friday compensable day. Defaults to 8.

		Returns:
			None: Initialization stores the fiscal-year denominator and empty result
				state on the instance.

		Raises:
			ValueError: ``fiscal_year`` is empty, outside the supported date range, or
				``hours_per_day`` is empty or not positive.
			TypeError: An argument has an unsupported type.
		"""
		throw_if( 'fiscal_year', fiscal_year )
		throw_if( 'hours_per_day', hours_per_day )
		if isinstance( fiscal_year, bool ) or not isinstance( fiscal_year, int ):
			raise TypeError( 'Fiscal year must be an integer.' )
		if fiscal_year < 2 or fiscal_year > 9999:
			raise ValueError( 'Fiscal year must be between 2 and 9999.' )
		self.fiscal_year: int = fiscal_year
		self.hours_per_day: Decimal = to_decimal( 'hours_per_day', hours_per_day )
		if self.hours_per_day <= 0:
			raise ValueError( 'Hours per day must be greater than zero.' )
		self.start_date: date = date( fiscal_year - 1, 10, 1 )
		self.end_date: date = date( fiscal_year, 9, 30 )
		self.compensable_days: int = self.count_weekdays( )
		self.compensable_hours: Decimal = Decimal( self.compensable_days ) * self.hours_per_day
		self.method: str = ''
		self.regular_hours: Decimal = Decimal( '0' )
		self.fte: Decimal = Decimal( '0' )

	def regular_method( self, regular_hours: int | float | Decimal ) -> Decimal:
		"""Calculate FTEs using OMB's regular method.

		Purpose:
			Divides regular straight-time hours worked from October 1 through
			September 30 by the compensable hours in the same fiscal year.
			Compensable hours equal Monday-through-Friday days multiplied by the
			configured hours per day; federal holidays do not reduce the denominator.

		Args:
			regular_hours (int | float | Decimal): Qualifying straight-time hours for
				the fiscal year. Zero is valid.

		Returns:
			Decimal: Calculated FTE value without forced rounding.

		Raises:
			ValueError: ``regular_hours`` is empty or negative.
			TypeError: ``regular_hours`` is Boolean or not numeric.
		"""
		hours = self.nonnegative_hours( regular_hours )
		self.method = 'regular'
		self.regular_hours = hours
		self.fte = hours / self.compensable_hours
		return self.fte

	def pay_period_method( self, selected_regular_hours: int | float | Decimal ) -> Decimal:
		"""Calculate FTEs using OMB's pay-period method.

		Purpose:
			Divides regular straight-time hours from the 26 biweekly pay periods
			ending in the fiscal year by 2,080. When 27 pay periods end in a fiscal
			year, OMB requires the caller to omit the period with the fewest workdays
			within that fiscal year before supplying the remaining 26-period total.

		Args:
			selected_regular_hours (int | float | Decimal): Qualifying straight-time
				hours from the 26 selected pay periods. Zero is valid.

		Returns:
			Decimal: Calculated FTE value without forced rounding.

		Raises:
			ValueError: ``selected_regular_hours`` is empty or negative.
			TypeError: ``selected_regular_hours`` is Boolean or not numeric.
		"""
		hours = self.nonnegative_hours( selected_regular_hours,
			name='selected_regular_hours' )
		self.method = 'pay_period'
		self.regular_hours = hours
		self.fte = hours / self.PAY_PERIOD_COMPENSABLE_HOURS
		return self.fte

	def hours_for_regular_fte( self, fte: int | float | Decimal ) -> Decimal:
		"""Return the regular-method hours represented by an FTE amount.

		Purpose:
			Converts a planned or reported FTE level to the corresponding number of
			regular straight-time hours for this fiscal year's denominator.

		Args:
			fte (int | float | Decimal): Nonnegative FTE amount to convert.

		Returns:
			Decimal: Required regular-method hours without forced rounding.

		Raises:
			ValueError: ``fte`` is empty or negative.
			TypeError: ``fte`` is Boolean or not numeric.
		"""
		fte_value = self.nonnegative_decimal( 'fte', fte )
		return fte_value * self.compensable_hours

	def hours_for_pay_period_fte( self, fte: int | float | Decimal ) -> Decimal:
		"""Return the pay-period-method hours represented by an FTE amount.

		Purpose:
			Converts a planned or reported FTE level to qualifying straight-time
			hours using OMB's fixed 2,080-hour pay-period denominator.

		Args:
			fte (int | float | Decimal): Nonnegative FTE amount to convert.

		Returns:
			Decimal: Required pay-period-method hours without forced rounding.

		Raises:
			ValueError: ``fte`` is empty or negative.
			TypeError: ``fte`` is Boolean or not numeric.
		"""
		fte_value = self.nonnegative_decimal( 'fte', fte )
		return fte_value * self.PAY_PERIOD_COMPENSABLE_HOURS

	def to_dict( self ) -> Dict[ str, object ]:
		"""Return the calculator state as a serializable mapping.

		Purpose:
			Provides the fiscal-year denominator and most recent result in a stable
			mapping suitable for application responses, reports, or data-frame rows.
			Decimal values are emitted as strings so serialization does not silently
			lose precision.

		Returns:
			Dict[str, object]: Fiscal-year dates, denominator, method, input hours,
				and calculated FTE.
		"""
		return {
			'fiscal_year': self.fiscal_year,
			'start_date': self.start_date.isoformat( ),
			'end_date': self.end_date.isoformat( ),
			'compensable_days': self.compensable_days,
			'compensable_hours': str( self.compensable_hours ),
			'method': self.method,
			'regular_hours': str( self.regular_hours ),
			'fte': str( self.fte ),
		}

	def count_weekdays( self ) -> int:
		"""Count Monday-through-Friday days in the fiscal-year date range.

		Returns:
			int: Inclusive weekday count used by the regular-method denominator.
		"""
		days = (self.end_date - self.start_date).days + 1
		return sum( 1 for offset in range( days )
			if (self.start_date + timedelta( days=offset )).weekday( ) < 5 )

	@classmethod
	def nonnegative_decimal( cls, name: str,
		value: int | float | Decimal ) -> Decimal:
		"""Validate and normalize a nonnegative decimal argument.

		Args:
			name (str): Argument name used in validation messages.
			value (int | float | Decimal): Numeric value to normalize.

		Returns:
			Decimal: Validated nonnegative value.

		Raises:
			ValueError: The value is empty, non-finite, or negative.
			TypeError: The value is Boolean or not numeric.
		"""
		decimal_value = to_decimal( name, value )
		if decimal_value < 0:
			raise ValueError( f'{name.replace( "_", " " ).title( )} cannot be negative.' )
		return decimal_value

	@classmethod
	def nonnegative_hours( cls, value: int | float | Decimal,
		name: str='regular_hours' ) -> Decimal:
		"""Validate and normalize an hours argument.

		Args:
			value (int | float | Decimal): Hours value to normalize.
			name (str): Argument name used in validation messages.

		Returns:
			Decimal: Validated nonnegative hours.

		Raises:
			ValueError: The value is empty, non-finite, or negative.
			TypeError: The value is Boolean or not numeric.
		"""
		return cls.nonnegative_decimal( name, value )
