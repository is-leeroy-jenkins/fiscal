"""Shared input normalization and validation utilities.

This module contains the small, dependency-free helpers used across Fiscal's
domain modules. Keeping them here avoids circular imports while preserving the
public imports exposed by :mod:`fiscal`.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Dict, Optional


_WEEKDAY_NAMES: Dict[ str, int ] = {
	'MONDAY': calendar.MONDAY,
	'TUESDAY': calendar.TUESDAY,
	'WEDNESDAY': calendar.WEDNESDAY,
	'THURSDAY': calendar.THURSDAY,
	'FRIDAY': calendar.FRIDAY,
	'SATURDAY': calendar.SATURDAY,
	'SUNDAY': calendar.SUNDAY,
}


def weekday_number( value: int | str ) -> int:
	"""Resolve a weekday name or number.

	Purpose:
		Converts a full English weekday name or an integer from 0 through 6 into the
		weekday number used internally by Python date objects.

	Args:
		value (int | str): Full weekday name or weekday number where Monday is 0.

	Returns:
		int: Weekday number from 0 through 6.

	Raises:
		TypeError: The supplied value is not an integer or string.
		ValueError: The supplied weekday name or number is invalid.
	"""
	if isinstance( value, bool ):
		raise TypeError( 'Weekday cannot be a Boolean value.' )
	if isinstance( value, int ):
		if value < calendar.MONDAY or value > calendar.SUNDAY:
			raise ValueError( 'Weekday must be between 0 and 6.' )
		return value
	if isinstance( value, str ):
		weekday_name = value.strip( ).upper( )
		if weekday_name not in _WEEKDAY_NAMES:
			raise ValueError( f'Unsupported weekday: {value}' )
		return _WEEKDAY_NAMES[ weekday_name ]
	raise TypeError( f'Unsupported weekday value: {type( value ).__name__}' )


def throw_if( name: str, value: object ) -> None:
	"""Validate a required argument.

	Purpose:
		Raises ``ValueError`` when a required argument is ``None``, an empty string,
		or an empty collection. Numeric zero and ``False`` remain valid values.

	Args:
		name (str): Name of the argument being validated.
		value (object): Argument value to validate.

	Returns:
		None: Validation does not return a value.

	Raises:
		ValueError: The supplied value is empty.
	"""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, (list, tuple, dict, set) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


def to_date( value: date | datetime | str | None ) -> Optional[ date ]:
	"""Convert a supported value to ``datetime.date``.

	Purpose:
		Converts date objects, datetime objects, ISO date text, and month/day/year text
		into a ``datetime.date`` value. Database sentinel values resolve to ``None``.

	Args:
		value (date | datetime | str | None): Value to convert.

	Returns:
		date | None: Converted date or ``None`` for a database sentinel value.

	Raises:
		ValueError: The supplied text cannot be parsed as a supported date.
		TypeError: The supplied value is not a supported date type.
	"""
	if value is None:
		return None
	if isinstance( value, datetime ):
		return value.date( )
	if isinstance( value, date ):
		return value
	if isinstance( value, str ):
		text = value.strip( )
		if text.upper( ) in ('', 'NS', 'N/A', 'NA', 'NONE', 'NULL'):
			return None
		for date_format in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y'):
			try:
				return datetime.strptime( text, date_format ).date( )
			except ValueError:
				continue
		raise ValueError( f'Unsupported date text: {text}' )
	raise TypeError( f'Unsupported date value: {type( value ).__name__}' )
