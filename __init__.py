'''
    ******************************************************************************************
      Assembly:                fiscal
      Filename:                init.py
      Author:                  Terry D. Eppler
      Created:                 08-26-2025

      Last Modified By:        Terry D. Eppler
      Last Modified On:        08-26-2025
    ******************************************************************************************
    <copyright file="init.py" company="Terry D. Eppler">

         Budget Fiscal Year Tools

     Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the “Software”),
     to deal in the Software without restriction,
     including without limitation the rights to use,
     copy, modify, merge, publish, distribute, sublicense,
     and/or sell copies of the Software,
     and to permit persons to whom the Software is furnished to do so,
     subject to the following conditions:

     The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.

     THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
     INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT.
     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
     ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
     DEALINGS IN THE SOFTWARE.

     You can contact me at:  terryeppler@gmail.com or eppler.terry@epa.gov

    </copyright>
    <summary>
        init.py
    </summary>
    ******************************************************************************************
'''

from __future__ import annotations
import calendar
import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import config as cfg
from boogr import Error

__all__: tuple[ str, ... ] = ('DB', 'FederalHoliday', 'FiscalYear', 'throw_if', 'to_date',)

_WEEKDAY_NAMES: Dict[ str, int ] = { 'MONDAY': calendar.MONDAY, 'TUESDAY': calendar.TUESDAY,
	'WEDNESDAY': calendar.WEDNESDAY, 'THURSDAY': calendar.THURSDAY, 'FRIDAY': calendar.FRIDAY,
	'SATURDAY': calendar.SATURDAY, 'SUNDAY': calendar.SUNDAY, }

def _weekday_number( value: int | str ) -> int:
	"""Resolve a weekday name or number.

	Purpose:
		Converts a full English weekday name or an integer from 0 through 6 into the weekday
		number used internally by Python date objects.

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
		Raises ``ValueError`` when a required argument is ``None``, an empty string, or an empty
		collection.

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
		Converts date objects, datetime objects, ISO date text, and month/day/year text into a
		``datetime.date`` value. Database sentinel values resolve to ``None``.

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

class DB( ):
	"""SQLite data-access base class.

	Purpose:
		Provides the configured SQLite database path, approved table names, active table selection,
		query state, database connection creation, and parameterized retrieval operations used by
		the
		fiscal-year domain entities.

	Attributes:
		path (str): Configured SQLite database path.
		tables (List[str]): Configured database table names.
		name (str): Active approved database table name.
		data (pd.DataFrame | None): Most recent query result.
		query_name (str): Table name assigned by the current query operation.
		query_fy (str): Fiscal-year value assigned by the current query operation.
		query_bpoa (str): Beginning period of availability assigned by a fiscal-year query.
		query_epoa (str): Ending period of availability assigned by a fiscal-year query.
		table_name (str): Candidate table name validated before query execution.
		"""
	
	path: Optional[ str ]
	tables: Optional[ List[ str ] ]
	name: Optional[ str ]
	data: Optional[ pd.DataFrame ]
	
	def __init__( self ) -> None:
		"""Initialize database configuration.

		Purpose:
			Loads the SQLite database path and approved table names from ``config.py`` and
			initializes
			the query-state members used by database operations.

		Returns:
			None: Initialization does not return a value.

		Raises:
			AttributeError: Required configuration members are not defined.
			TypeError: The configured table collection cannot be converted to a list."""
		self.path = cfg.DB_PATH
		self.tables = cfg.TABLES
	
	def __dir__( self ) -> List[ str ]:
		"""Return public database members."""
		return [ 'path', 'tables', 'name', 'data', 'create_connection', 'query_year',
			'query_holiday' ]
	
	def create_connection( self ) -> sqlite3.Connection:
		"""Create a SQLite database connection.

		Purpose:
			Opens the SQLite database configured by ``cfg.DB_PATH``.

		Returns:
			sqlite3.Connection: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return sqlite3.connect( self.path )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'DB'
			ex.method = 'create_connection( self ) -> sqlite3.Connection'
			raise ex
	
	def query_year( self, name: str, fy: str, bpoa: str, epoa: str ) -> pd.DataFrame:
		"""Query one fiscal-year row.

		Purpose:
			Retrieves the ``BudgetFiscalYears`` row matching the supplied fiscal year and period
			        of availability values.

		Args:
			name (str): Value used by the operation.
			fy (str): Value used by the operation.
			bpoa (str): Value used by the operation.
			epoa (str): Value used by the operation.

		Returns:
			pd.DataFrame: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'name', name )
			throw_if( 'fy', fy )
			throw_if( 'bpoa', bpoa )
			throw_if( 'epoa', epoa )
			self.name = name
			if self.name not in self.tables:
				raise ValueError( f'Unsupported table: {self.name}' )
			sql = (f'SELECT * FROM "{self.name}" '
			       'WHERE FiscalYear = ? AND BPOA = ? AND EPOA = ?;')
			parameters = (fy, bpoa, epoa)
			with self.create_connection( ) as connection:
				self.data = pd.read_sql_query( sql, connection, params=parameters )
			if len( self.data.index ) != 1:
				raise LookupError(
					f'Expected one {self.name} row; found {len( self.data.index )}.' )
			return self.data.copy( )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'DB'
			ex.method = ('query_year( self, name: str, fy: str, bpoa: str, epoa: str ) -> '
			             'pd.DataFrame')
			raise ex
	
	def query_holiday( self, name: str, fy: str ) -> pd.DataFrame:
		"""Query one federal-holiday row.

		Purpose:
			Retrieves the ``FederalHolidays`` row matching the supplied fiscal year.

		Args:
			name (str): Value used by the operation.
			fy (str): Value used by the operation.

		Returns:
			pd.DataFrame: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'name', name )
			throw_if( 'fy', fy )
			self.name = name
			if self.name not in self.tables:
				raise ValueError( f'Unsupported table: {self.name}' )
			sql = f'SELECT * FROM "{self.name}" WHERE FiscalYear = ?;'
			parameters = (fy,)
			with self.create_connection( ) as connection:
				self.data = pd.read_sql_query( sql, connection, params=parameters )
			if len( self.data.index ) != 1:
				raise LookupError(
					f'Expected one {self.name} row; found {len( self.data.index )}.' )
			return self.data.copy( )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'DB'
			ex.method = 'query_federal_holiday( self, name: str, fy: str ) -> pd.DataFrame'
			raise ex

class FiscalYear( DB ):
	"""Budget fiscal-year database entity.

	Purpose:
		Maps one ``BudgetFiscalYears`` database row to typed properties and provides calendar-year,
		fiscal-year, holiday, weekend, and workday calculations derived from that row and the
		current calculation date.

	Attributes:
		holidays (List[ Dict[ str str ] ]):  List of holidays for a given fiscal year
		range_start (date | None): Normalized start date assigned by range-counting methods.
		range_end (date | None): Normalized end date assigned by range-counting methods.
		use_observed (bool): Indicates whether observed holiday dates are used.
		id (int): Read-only database row identifier.
		fiscal_year (str): Read-only fiscal-year identifier.
		bpoa (str): Read-only beginning period of availability.
		epoa (str): Read-only ending period of availability.
		start_date (date): Read-only fiscal-year start date.
		end_date (date | None): Read-only fiscal-year end date.
		expiration_date (date | None): Read-only appropriation expiration date.
		cancellation_date (date | None): Read-only appropriation cancellation date.
		weekdays (int): Read-only number of weekdays stored in the database row.
		weekends (int): Read-only number of weekend days stored in the database row.
		workdays (float): Read-only number of workdays stored in the database row.
		compensable_days (float): Read-only number of compensable days.
		compensable_workdays (float): Legacy read-only alias for ``compensable_days``.
		compensable_hours (float): Read-only number of compensable hours.
		type (str): Read-only appropriation type.
		availability (str): Read-only appropriation availability description.
		current_date (date): Read-only date used by calendar and fiscal calculations.
		calendar_year (int): Read-only calendar year containing ``current_date``.
		cy_start_date (date): Read-only first date of ``calendar_year``.
		cy_end_date (date): Read-only final date of ``calendar_year``.
		date (date): Read-only alias for ``current_date``.
		"""
	id: Optional[ int ]
	fiscal_year: Optional[ str ]
	bpoa: Optional[ str ]
	epoa: Optional[ str ]
	start_date: Optional[ date ]
	end_date: Optional[ date ]
	expiration_date: Optional[ date ]
	cancellation_date: Optional[ date ]
	weekdays: Optional[ int ]
	weekends: Optional[ int ]
	workdays: Optional[ float ]
	compensable_days: Optional[ float ]
	compensable_workdays: Optional[ int ]
	compensable_hours: Optional[ int ]
	type: Optional[ str ]
	availability: Optional[ str ]
	current_date: Optional[ date ]
	calendar_year: Optional[ int ]
	cy_start_date: Optional[ date ]
	cy_end_date: Optional[ date ]
	range_start: Optional[ date ]
	range_end: Optional[ date ]
	use_observed: Optional[ bool ]
	
	def __init__( self, fy: str | int, bpoa: str | int = '', epoa: str | int = '' ) -> None:
		"""Initialize a budget fiscal-year entity.

		Purpose:
			Retrieves one fiscal-year record and initializes calendar calculations using the
			current system date returned by ``datetime.today().date()``.

		Args:
			fy (str | int): Fiscal year used to retrieve the database row.
			bpoa (str | int): Beginning period of availability. An empty value defaults to ``fy``.
			epoa (str | int): Ending period of availability. An empty value defaults to ``fy``.

		Returns:
			None: Initialization does not return a value.
		"""
		super( ).__init__( )
		throw_if( 'fy', fy )
		self.fiscal_year = str( fy )
		self.bpoa = str( bpoa ) if bpoa != '' else self.fiscal_year
		self.epoa = str( epoa ) if epoa != '' else self.fiscal_year
		self.name = self.tables[ 0 ]
		df = self.query_year( self.name, self.fiscal_year, self.bpoa, self.epoa )
		row = df.iloc[ 0 ]
		self.id = int( row[ 'ID' ] )
		self.fiscal_year = str( row[ 'FiscalYear' ] )
		self.bpoa = str( row[ 'BPOA' ] )
		self.epoa = str( row[ 'EPOA' ] )
		self.start_date = to_date( row[ 'StartDate' ] )
		self.end_date = to_date( row[ 'EndDate' ] )
		self.expiration_date = to_date( row[ 'ExpirationDate' ] )
		self.cancellation_date = to_date( row[ 'CancellationDate' ] )
		self.weekdays = int( row[ 'Weekdays' ] )
		self.weekends = int( row[ 'Weekends' ] )
		self.workdays = float( row[ 'Workdays' ] )
		self.compensable_days = float( row[ 'CompensableDays' ] )
		self.compensable_workdays = self.compensable_days
		self.compensable_hours = float( row[ 'CompensableHours' ] )
		self.type = str( row[ 'Type' ] )
		self.availability = str( row[ 'Availability' ] )
		self.current_date = datetime.today( ).date( )
		self.calendar_year = self.current_date.year
		self.cy_start_date = date( self.calendar_year, 1, 1 )
		self.cy_end_date = date( self.calendar_year, 12, 31 )
	
	def __repr__( self ) -> str:
		"""Return the fiscal-year identifier.

		Purpose:
			Return the fiscal-year identifier.

		Returns:
			str: Value produced by the operation."""
		return self.fiscal_year
	
	def __dir__( self ) -> List[ str ]:
		"""Return public fiscal-year members.

		Purpose:
			Returns the public database fields, fiscal and calendar calculations, date collections,
			period summaries, holiday mappings, and range-counting operations exposed by the
			entity.

		Returns:
			List[str]: Public member names available from the fiscal-year entity.
		"""
		return [ 'id', 'fiscal_year', 'bpoa', 'epoa', 'start_date', 'end_date', 'expiration_date',
			'cancellation_date', 'weekdays', 'weekends', 'workdays', 'compensable_days',
			'compensable_workdays', 'compensable_hours', 'type', 'availability', 'current_date',
			'calendar_year', 'cy_start_date', 'cy_end_date', 'holidays', 'calendar_day_of_year',
			'calendar_days_elapsed', 'calendar_days_remaining', 'calendar_months_elapsed',
			'calendar_months_remaining', 'calendar_percent_elapsed', 'calendar_days_in_year',
			'calendar_week_number', 'calendar_month_name', 'calendar_bounds', 'fiscal_day_of_year',
			'fiscal_month_number', 'fiscal_days_elapsed', 'fiscal_days_remaining',
			'fiscal_months_elapsed', 'fiscal_months_remaining', 'fiscal_percent_elapsed',
			'fiscal_days_in_year', 'fiscal_month_bounds', 'fiscal_days_in_month',
			'fiscal_month_calendar', 'fiscal_month_weeks', 'fiscal_month_text_calendar',
			'fiscal_year_text_calendar', 'date_range_text_calendar', 'fiscal_month_html_calendar',
			'fiscal_year_html_calendar', 'date_range_html_calendar', 'fiscal_month_name',
			'fiscal_quarter_number', 'fiscal_quarter_bounds', 'fiscal_days_in_quarter',
			'fiscal_week_number', 'fiscal_week_bounds', 'fiscal_dates', 'fiscal_weekdays',
			'fiscal_weekends', 'fiscal_workdays', 'fiscal_calendar', 'weekdays_in_month',
			'weekends_in_month', 'weekday_occurrences', 'weekdays_by_month', 'weekends_by_month',
			'workdays_by_month', 'holidays_by_month', 'holiday_dates_between', 'holidays_between',
			'dates_by_month', 'fiscal_month_dates', 'fiscal_month_day_numbers',
			'holidays_remaining', 'workdays_remaining', 'weekends_remaining', 'contains_leap_day',
			'leap_days_in_availability', 'current_weekday_name', 'count_weekends',
			'count_holidays',
			'count_workdays', 'fiscal_bounds', 'is_fiscal_start_year', 'is_fiscal_end_year',
			'is_calendar_start_year', 'is_calendar_end_date', 'to_dict' ]
	
	@property
	def holidays( self ) -> List[ Dict[ str, str ] ]:
		"""Return the FederalHolidays row as column-and-value mappings.
	
		Purpose:
			Queries the ``FederalHolidays`` table for the fiscal year represented by this instance
			and converts the matching row into a list of dictionaries. Each dictionary contains one
			holiday name and its corresponding value.
	
		Returns:
			List[Dict[str, str]]: Federal holiday column names and values for the current fiscal
			year.
				Each item contains ``ColumnName`` and ``ColumnValue`` keys.
	
		Raises:
			Error: The FederalHolidays row cannot be queried or converted.
		"""
		try:
			self.holiday_table_name = self.tables[ 1 ]
			self.holiday_data = self.query_holiday( name=self.holiday_table_name,
				fy=self.fiscal_year )
			self.holiday_row = self.holiday_data.iloc[ 0 ]
			self.holiday_columns = [ column for column in self.holiday_data.columns if
				column not in ('ID', 'FiscalYear') ]
			
			return [ { str( column ): ('' if pd.isna( self.holiday_row[ column ] ) else str(
				self.holiday_row[ column ] )) } for column in self.holiday_columns ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'holidays( self ) -> List[ Dict[ str, str ] ]'
			raise ex
	
	def calendar_day_of_year( self ) -> int:
		"""Return the one-based calendar day-of-year index.

		Purpose:
			Return the one-based calendar day-of-year index.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return (self.current_date - self.cy_start_date).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_day_of_year( self ) -> int'
			raise ex
	
	def calendar_days_elapsed( self ) -> int:
		"""Return elapsed calendar-year days.

		Purpose:
			Return elapsed calendar-year days.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return max( 0, (self.current_date - self.cy_start_date).days )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_days_elapsed( self ) -> int'
			raise ex
	
	def calendar_days_remaining( self ) -> int:
		"""Return remaining calendar-year days.

		Purpose:
			Return remaining calendar-year days.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return max( 0, (self.cy_end_date - self.current_date).days )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_days_remaining( self ) -> int'
			raise ex
	
	def calendar_months_elapsed( self ) -> int:
		"""Return elapsed calendar-year months.

		Purpose:
			Return elapsed calendar-year months.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return self.current_date.month - 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_elapsed_months( self ) -> int'
			raise ex
	
	def calendar_months_remaining( self ) -> int:
		"""Return remaining calendar-year months.

		Purpose:
			Return remaining calendar-year months.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return 12 - self.current_date.month
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_remaining_months( self ) -> int'
			raise ex
	
	def calendar_percent_elapsed( self ) -> float:
		"""Return the elapsed calendar-year percentage.

		Purpose:
			Return the elapsed calendar-year percentage.

		Returns:
			float: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return (self.calendar_days_elapsed( ) / self.calendar_days_in_year( )) * 100.0
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_percent_elapsed( self ) -> float'
			raise ex
	
	def fiscal_day_of_year( self ) -> int:
		"""Return the one-based fiscal day-of-year index.

		Purpose:
			Return the one-based fiscal day-of-year index.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return (self.current_date - self.start_date).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_day_of_year( self ) -> int'
			raise ex
	
	def fiscal_month_number( self ) -> int:
		"""Return the federal fiscal-month number.

		Purpose:
			Return the federal fiscal-month number.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return ((self.current_date.month - 10) % 12) + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_number( self ) -> int'
			raise ex
	
	def fiscal_days_elapsed( self ) -> int:
		"""Return elapsed fiscal-year days.

		Purpose:
			Return elapsed fiscal-year days.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return max( 0, (self.current_date - self.start_date).days )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_days_elapsed( self ) -> int'
			raise ex
	
	def fiscal_days_remaining( self ) -> int:
		"""Return remaining fiscal-year days.

		Purpose:
			Return remaining fiscal-year days.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'end_date', self.end_date )
			return max( 0, (self.end_date - self.current_date).days )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_days_remaining( self ) -> int'
			raise ex
	
	def fiscal_months_elapsed( self ) -> int:
		"""Return elapsed fiscal-year months.

		Purpose:
			Return elapsed fiscal-year months.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return self.fiscal_month_number( ) - 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_months_elapsed( self ) -> int'
			raise ex
	
	def fiscal_months_remaining( self ) -> int:
		"""Return remaining fiscal-year months.

		Purpose:
			Return remaining fiscal-year months.

		Returns:
			int: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return 12 - self.fiscal_month_number( )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_months_remaining( self ) -> int'
			raise ex
	
	def fiscal_percent_elapsed( self ) -> float:
		"""Return the elapsed fiscal-year percentage.

		Purpose:
			Return the elapsed fiscal-year percentage.

		Returns:
			float: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return (self.fiscal_days_elapsed( ) / self.fiscal_days_in_year( )) * 100.0
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_percent_elapsed( self ) -> float'
			raise ex
	
	def _fiscal_range( self, start: date | datetime, end: date | datetime ) -> Tuple[ date, date ]:
		"""Return a validated range clamped to the represented fiscal year."""
		throw_if( 'start', start )
		throw_if( 'end', end )
		range_start = to_date( start )
		range_end = to_date( end )
		throw_if( 'range_start', range_start )
		throw_if( 'range_end', range_end )
		if range_start > range_end:
			raise ValueError( 'Start date cannot be later than end date.' )
		clamped_start = max( range_start, self.start_date )
		clamped_end = min( range_end, self.end_date )
		if clamped_start > clamped_end:
			raise ValueError( 'The supplied range does not intersect the represented fiscal '
			                  'year.' )
		return clamped_start, clamped_end
	
	def count_weekends( self, start: date | datetime, end: date | datetime ) -> int:
		"""Count weekend days in an inclusive fiscal-year range."""
		try:
			range_start, range_end = self._fiscal_range( start, end )
			self.range_start = range_start
			self.range_end = range_end
			count = 0
			current = range_start
			while current <= range_end:
				if current.weekday( ) >= 5:
					count += 1
				current += timedelta( days=1 )
			return count
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('count_weekends( self, start: date | datetime, end: date | datetime ) -> '
			             'int')
			raise ex
	
	def calendar_days_in_year( self ) -> int:
		try:
			return (self.cy_end_date - self.cy_start_date).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_days_in_year( self ) -> int'
			raise ex
	
	def fiscal_days_in_year( self ) -> int:
		try:
			return (self.end_date - self.start_date).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_days_in_year( self ) -> int'
			raise ex
	
	def count_holidays( self, start: date | datetime, end: date | datetime,
		use_observed: bool = True ) -> int:
		"""Count federal holidays in an inclusive fiscal-year range."""
		try:
			range_start, range_end = self._fiscal_range( start, end )
			self.range_start = range_start
			self.range_end = range_end
			self.use_observed = use_observed
			federal_holiday = FederalHoliday( self.fiscal_year )
			key = 'observed' if use_observed else 'actual'
			return sum( 1 for payload in federal_holiday.holidays( ).values( ) if
				range_start <= payload[ key ] <= range_end )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('count_holidays( self, start: date | datetime, end: date | datetime, '
			             'use_observed: bool = True ) -> int')
			raise ex
	
	def count_workdays( self, start: date | datetime, end: date | datetime,
		use_observed: bool = True ) -> int:
		"""Count workdays in an inclusive fiscal-year range."""
		try:
			range_start, range_end = self._fiscal_range( start, end )
			self.range_start = range_start
			self.range_end = range_end
			self.use_observed = use_observed
			federal_holiday = FederalHoliday( self.fiscal_year )
			key = 'observed' if use_observed else 'actual'
			holiday_dates = { payload[ key ] for payload in federal_holiday.holidays( ).values( ) }
			count = 0
			current = range_start
			while current <= range_end:
				if current.weekday( ) < 5 and current not in holiday_dates:
					count += 1
				current += timedelta( days=1 )
			return count
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('count_workdays( self, start: date | datetime, end: date | datetime, '
			             'use_observed: bool = True ) -> int')
			raise ex
	
	def calendar_bounds( self ) -> Tuple[ date, date ]:
		"""Return calendar-year boundaries.

		Purpose:
			Return calendar-year boundaries.

		Returns:
			Tuple[date, date]: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return self.cy_start_date, self.cy_end_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_bounds( self ) -> Tuple[ date, date ]'
			raise ex
	
	def fiscal_bounds( self ) -> Tuple[ date, date ]:
		"""Return fiscal-year boundaries.

		Purpose:
			Return fiscal-year boundaries.

		Returns:
			Tuple[date, date]: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'end_date', self.end_date )
			return self.start_date, self.end_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_bounds( self ) -> Tuple[ date, date ]'
			raise ex
	
	def is_fiscal_start_year( self ) -> bool:
		"""Determine whether the calculation date starts the fiscal year."""
		try:
			return self.current_date == self.start_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'is_fiscal_start_year( self ) -> bool'
			raise ex
	
	def is_fiscal_end_year( self ) -> bool:
		"""Determine whether the calculation date ends the fiscal year."""
		try:
			return self.current_date == self.end_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'is_fiscal_end_year( self ) -> bool'
			raise ex
	
	def is_calendar_start_year( self ) -> bool:
		"""Determine whether the calculation date starts the calendar year."""
		try:
			return self.current_date == self.cy_start_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'is_calendar_start_year( self ) -> bool'
			raise ex
	
	def is_calendar_end_date( self ) -> bool:
		"""Determine whether the current date ends the calendar year.

		Purpose:
			Determine whether the current date ends the calendar year.

		Returns:
			bool: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return self.current_date == self.cy_end_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'is_calendar_end_date( self ) -> bool'
			raise ex
	
	def fiscal_month_bounds( self, fiscal_month: int ) -> Tuple[ date, date ]:
		"""Return the boundaries of a federal fiscal month.

		Purpose:
			Maps a one-based federal fiscal-month number to its calendar month and returns the
			first
			and final dates of that month within the represented fiscal year.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12, where October is 1
				and September is 12.

		Returns:
			Tuple[date, date]: Inclusive first and final dates of the fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or the month boundaries cannot be calculated.
		"""
		try:
			throw_if( 'fiscal_month', fiscal_month )
			self.requested_fiscal_month = fiscal_month
			if self.requested_fiscal_month < 1 or self.requested_fiscal_month > 12:
				raise ValueError( 'Fiscal month must be between 1 and 12.' )
			calendar_month = ((self.requested_fiscal_month + 8) % 12) + 1
			calendar_year = self.start_date.year if calendar_month >= 10 else self.end_date.year
			last_day = calendar.monthrange( calendar_year, calendar_month )[ 1 ]
			return date( calendar_year, calendar_month, 1 ), date( calendar_year, calendar_month,
				last_day )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_bounds( self, fiscal_month: int ) -> Tuple[ date, date ]'
			raise ex
	
	def fiscal_days_in_month( self, fiscal_month: int ) -> int:
		"""Return the number of days in a federal fiscal month.

		Purpose:
			Returns the exact number of calendar days in a selected federal fiscal month, including
			leap-year effects for February.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			int: Number of calendar days in the selected fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or its boundaries cannot be calculated.
		"""
		try:
			month_start, month_end = self.fiscal_month_bounds( fiscal_month )
			return (month_end - month_start).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_days_in_month( self, fiscal_month: int ) -> int'
			raise ex
	
	def fiscal_month_calendar( self, fiscal_month: int ) -> List[ List[ date ] ]:
		"""Return a Monday-first date matrix for a federal fiscal month.

		Purpose:
			Builds complete Monday-through-Sunday week rows for a selected fiscal month. Leading
			and
			trailing dates from adjacent months are retained to preserve complete calendar weeks.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			List[List[date]]: Complete calendar-week rows containing date objects.

		Raises:
			Error: The fiscal-month number is invalid or the calendar matrix cannot be created.
		"""
		try:
			month_start, _ = self.fiscal_month_bounds( fiscal_month )
			month_calendar = calendar.Calendar( firstweekday=calendar.MONDAY )
			return month_calendar.monthdatescalendar( month_start.year, month_start.month )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_calendar( self, fiscal_month: int ) -> List[ List[ date ] ]'
			raise ex
	
	def fiscal_month_weeks( self, fiscal_month: int ) -> List[ List[ int ] ]:
		"""Return a Monday-first week matrix for a federal fiscal month.

		Purpose:
			Returns integer day-number rows for a selected fiscal month. Zero values identify
			positions
			that belong to adjacent calendar months.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			List[List[int]]: Week rows containing month day numbers and zero placeholders.

		Raises:
			Error: The fiscal-month number is invalid or the week matrix cannot be created.
		"""
		try:
			month_start, _ = self.fiscal_month_bounds( fiscal_month )
			month_calendar = calendar.Calendar( firstweekday=calendar.MONDAY )
			return month_calendar.monthdayscalendar( month_start.year, month_start.month )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_weeks( self, fiscal_month: int ) -> List[ List[ int ] ]'
			raise ex
	
	def fiscal_month_text_calendar( self, fiscal_month: int ) -> str:
		"""Return a plain-text calendar for a federal fiscal month.

		Purpose:
			Renders the selected federal fiscal month using ``calendar.TextCalendar`` with Monday
			as the first weekday.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			str: Plain-text calendar for the selected fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or the text calendar cannot be rendered.
		"""
		try:
			month_start, _ = self.fiscal_month_bounds( fiscal_month )
			text_calendar = calendar.TextCalendar( firstweekday=calendar.MONDAY )
			return text_calendar.formatmonth( month_start.year, month_start.month )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_text_calendar( self, fiscal_month: int ) -> str'
			raise ex
	
	def fiscal_year_text_calendar( self ) -> str:
		"""Return a plain-text calendar for the represented federal fiscal year.

		Purpose:
			Renders October through September using ``calendar.TextCalendar`` while preserving
			federal fiscal-month order.

		Returns:
			str: Plain-text calendars for all twelve federal fiscal months.

		Raises:
			Error: A fiscal-month boundary is unavailable or the text calendar cannot be rendered.
		"""
		try:
			return '\n'.join(
				self.fiscal_month_text_calendar( fiscal_month ).rstrip( ) for fiscal_month in
				range( 1, 13 ) ) + '\n'
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_year_text_calendar( self ) -> str'
			raise ex
	
	def fiscal_month_html_calendar( self, fiscal_month: int, with_year: bool = True ) -> str:
		"""Return an HTML table for a federal fiscal month.

		Purpose:
			Renders the selected federal fiscal month using ``calendar.HTMLCalendar`` with Monday
			as the first weekday.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.
			with_year (bool): Includes the calendar year in the month heading when ``True``.

		Returns:
			str: HTML calendar table for the selected fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or the HTML calendar cannot be rendered.
		"""
		try:
			month_start, _ = self.fiscal_month_bounds( fiscal_month )
			html_calendar = calendar.HTMLCalendar( firstweekday=calendar.MONDAY )
			return html_calendar.formatmonth( month_start.year, month_start.month,
				withyear=with_year )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('fiscal_month_html_calendar( self, fiscal_month: int, '
			             'with_year: bool = True ) -> str')
			raise ex
	
	def fiscal_year_html_calendar( self, width: int = 3 ) -> str:
		"""Return HTML tables for the represented federal fiscal year.

		Purpose:
			Renders October through September in federal fiscal-month order using
			``calendar.HTMLCalendar``. The tables are grouped into rows containing the requested
			number of months.

		Args:
			width (int): Number of month tables placed in each HTML row.

		Returns:
			str: HTML table containing all twelve federal fiscal months.

		Raises:
			Error: ``width`` is invalid or the HTML calendar cannot be rendered.
		"""
		try:
			throw_if( 'width', width )
			if isinstance( width, bool ) or not isinstance( width, int ):
				raise TypeError( 'Width must be an integer.' )
			if width < 1 or width > 12:
				raise ValueError( 'Width must be between 1 and 12.' )
			month_tables = [ self.fiscal_month_html_calendar( fiscal_month ) for fiscal_month in
				range( 1, 13 ) ]
			rows = [ month_tables[ index:index + width ] for index in range( 0, 12, width ) ]
			row_html = [ '<tr>' + ''.join( f'<td>{month}</td>' for month in row ) + '</tr>' for row
				in rows ]
			return '<table class="fiscal-year">' + ''.join( row_html ) + '</table>'
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_year_html_calendar( self, width: int = 3 ) -> str'
			raise ex
	
	def date_range_text_calendar( self, start: date | datetime, end: date | datetime ) -> str:
		"""Return plain-text calendars spanning an inclusive fiscal-year date range.

		Purpose:
			Renders every calendar month intersecting the supplied inclusive range using
			``calendar.TextCalendar`` with Monday as the first weekday. The supplied range is
			validated and constrained to the represented fiscal year.

		Args:
			start (date | datetime): Inclusive beginning date.
			end (date | datetime): Inclusive ending date.

		Returns:
			str: Plain-text month calendars in chronological order.

		Raises:
			Error: The date range is invalid or the text calendars cannot be rendered.
		"""
		try:
			range_start, range_end = self._fiscal_range( start, end )
			text_calendar = calendar.TextCalendar( firstweekday=calendar.MONDAY )
			calendar_year = range_start.year
			calendar_month = range_start.month
			calendars: List[ str ] = [ ]
			while (calendar_year, calendar_month) <= (range_end.year, range_end.month):
				calendars.append(
					text_calendar.formatmonth( calendar_year, calendar_month ).rstrip( ) )
				if calendar_month == 12:
					calendar_year += 1
					calendar_month = 1
				else:
					calendar_month += 1
			return '\n'.join( calendars ) + '\n'
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('date_range_text_calendar( self, start: date | datetime, '
			             'end: date | datetime ) -> str')
			raise ex
	
	def date_range_html_calendar( self, start: date | datetime, end: date | datetime,
		width: int = 3, with_year: bool = True ) -> str:
		"""Return HTML month tables spanning an inclusive fiscal-year date range.

		Purpose:
			Renders every calendar month intersecting the supplied inclusive range using
			``calendar.HTMLCalendar`` with Monday as the first weekday. The supplied range is
			validated and constrained to the represented fiscal year. Month tables are grouped into
			rows containing the requested number of months.

		Args:
			start (date | datetime): Inclusive beginning date.
			end (date | datetime): Inclusive ending date.
			width (int): Number of month tables placed in each HTML row.
			with_year (bool): Includes the calendar year in each month heading when ``True``.

		Returns:
			str: HTML table containing the rendered month calendars in chronological order.

		Raises:
			Error: The date range or width is invalid, or the HTML calendars cannot be rendered.
		"""
		try:
			throw_if( 'width', width )
			if isinstance( width, bool ) or not isinstance( width, int ):
				raise TypeError( 'Width must be an integer.' )
			if width < 1 or width > 12:
				raise ValueError( 'Width must be between 1 and 12.' )
			range_start, range_end = self._fiscal_range( start, end )
			html_calendar = calendar.HTMLCalendar( firstweekday=calendar.MONDAY )
			calendar_year = range_start.year
			calendar_month = range_start.month
			month_tables: List[ str ] = [ ]
			while (calendar_year, calendar_month) <= (range_end.year, range_end.month):
				month_tables.append(
					html_calendar.formatmonth( calendar_year, calendar_month, withyear=with_year
					) )
				if calendar_month == 12:
					calendar_year += 1
					calendar_month = 1
				else:
					calendar_month += 1
			rows = [ month_tables[ index:index + width ] for index in
				range( 0, len( month_tables ), width ) ]
			row_html = [ '<tr>' + ''.join( f'<td>{month}</td>' for month in row ) + '</tr>' for row
				in rows ]
			return '<table class="fiscal-date-range">' + ''.join( row_html ) + '</table>'
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('date_range_html_calendar( self, start: date | datetime, '
			             'end: date | datetime, width: int = 3, with_year: bool = True ) -> str')
			raise ex
	
	def fiscal_quarter_number( self ) -> int:
		"""Return the federal fiscal-quarter number for the current date.

		Purpose:
			Maps the current federal fiscal-month number to quarter 1 through quarter 4.

		Returns:
			int: Federal fiscal-quarter number from 1 through 4.

		Raises:
			Error: The fiscal-quarter number cannot be calculated.
		"""
		try:
			return ((self.fiscal_month_number( ) - 1) // 3) + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_quarter_number( self ) -> int'
			raise ex
	
	def fiscal_quarter_bounds( self, quarter: int ) -> Tuple[ date, date ]:
		"""Return the boundaries of a federal fiscal quarter.

		Purpose:
			Returns the inclusive first and final dates of a selected federal fiscal quarter.

		Args:
			quarter (int): Federal fiscal-quarter number from 1 through 4.

		Returns:
			Tuple[date, date]: Inclusive first and final dates of the fiscal quarter.

		Raises:
			Error: The quarter number is invalid or its boundaries cannot be calculated.
		"""
		try:
			throw_if( 'quarter', quarter )
			self.requested_quarter = quarter
			if self.requested_quarter < 1 or self.requested_quarter > 4:
				raise ValueError( 'Fiscal quarter must be between 1 and 4.' )
			first_fiscal_month = ((self.requested_quarter - 1) * 3) + 1
			last_fiscal_month = first_fiscal_month + 2
			quarter_start, _ = self.fiscal_month_bounds( first_fiscal_month )
			_, quarter_end = self.fiscal_month_bounds( last_fiscal_month )
			return quarter_start, quarter_end
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_quarter_bounds( self, quarter: int ) -> Tuple[ date, date ]'
			raise ex
	
	def fiscal_days_in_quarter( self, quarter: int ) -> int:
		"""Return the number of days in a federal fiscal quarter.

		Purpose:
			Returns the inclusive number of calendar days in a selected fiscal quarter.

		Args:
			quarter (int): Federal fiscal-quarter number from 1 through 4.

		Returns:
			int: Number of calendar days in the selected fiscal quarter.

		Raises:
			Error: The quarter number is invalid or its boundaries cannot be calculated.
		"""
		try:
			quarter_start, quarter_end = self.fiscal_quarter_bounds( quarter )
			return (quarter_end - quarter_start).days + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_days_in_quarter( self, quarter: int ) -> int'
			raise ex
	
	def weekdays_in_month( self, fiscal_month: int ) -> int:
		"""Return the weekday count for a federal fiscal month.

		Purpose:
			Counts Monday-through-Friday dates in a selected federal fiscal month without excluding
			federal holidays.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			int: Number of weekday dates in the selected fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or the weekday count cannot be calculated.
		"""
		try:
			month_start, month_end = self.fiscal_month_bounds( fiscal_month )
			count = 0
			current = month_start
			while current <= month_end:
				if current.weekday( ) < 5:
					count += 1
				current += timedelta( days=1 )
			return count
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'weekdays_in_month( self, fiscal_month: int ) -> int'
			raise ex
	
	def weekends_in_month( self, fiscal_month: int ) -> int:
		"""Return the weekend-day count for a federal fiscal month.

		Purpose:
			Counts Saturday and Sunday dates in a selected federal fiscal month.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			int: Number of weekend dates in the selected fiscal month.

		Raises:
			Error: The fiscal-month number is invalid or the weekend count cannot be calculated.
		"""
		try:
			month_start, month_end = self.fiscal_month_bounds( fiscal_month )
			return self.count_weekends( month_start, month_end )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'weekends_in_month( self, fiscal_month: int ) -> int'
			raise ex
	
	def weekday_occurrences( self, fiscal_month: int, weekday: int | str ) -> int:
		"""Return the occurrence count of a weekday in a federal fiscal month.

		Purpose:
			Counts a weekday supplied as a full English name or the existing integer value.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.
			weekday (int | str): Full weekday name or integer where Monday is 0.

		Returns:
			int: Number of occurrences of the selected weekday.
		"""
		try:
			requested_weekday = _weekday_number( weekday )
			self.requested_weekday = requested_weekday
			month_start, month_end = self.fiscal_month_bounds( fiscal_month )
			count = 0
			current = month_start
			while current <= month_end:
				if current.weekday( ) == requested_weekday:
					count += 1
				current += timedelta( days=1 )
			return count
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('weekday_occurrences( self, fiscal_month: int, weekday: int | str ) -> '
			             'int')
			raise ex
	
	def contains_leap_day( self ) -> bool:
		"""Determine whether the represented fiscal year contains February 29.

		Purpose:
			Evaluates whether a leap day falls within the inclusive fiscal-year boundaries.

		Returns:
			bool: ``True`` when February 29 is within the represented fiscal year; otherwise
			``False``.

		Raises:
			Error: Fiscal-year boundaries are unavailable or the leap-day test fails.
		"""
		try:
			for calendar_year in range( self.start_date.year, self.end_date.year + 1 ):
				if calendar.isleap( calendar_year ):
					leap_day = date( calendar_year, 2, 29 )
					if self.start_date <= leap_day <= self.end_date:
						return True
			return False
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'contains_leap_day( self ) -> bool'
			raise ex
	
	def leap_days_in_availability( self ) -> int:
		"""Return the leap-day count in the period of availability.

		Purpose:
			Counts February 29 dates within the inclusive start and end dates represented by the
			fiscal-year database row.

		Returns:
			int: Number of leap days within the period of availability.

		Raises:
			Error: Availability boundaries are unavailable or the leap-day count fails.
		"""
		try:
			throw_if( 'start_date', self.start_date )
			throw_if( 'end_date', self.end_date )
			count = 0
			for calendar_year in range( self.start_date.year, self.end_date.year + 1 ):
				if calendar.isleap( calendar_year ):
					leap_day = date( calendar_year, 2, 29 )
					if self.start_date <= leap_day <= self.end_date:
						count += 1
			return count
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'leap_days_in_availability( self ) -> int'
			raise ex
	
	def calendar_week_number( self ) -> int:
		"""Return the ISO calendar-week number for the current date.

		Purpose:
			Returns the ISO 8601 week number containing the current calculation date.

		Returns:
			int: ISO calendar-week number from 1 through 53.

		Raises:
			Error: The current date is unavailable or the week number cannot be calculated.
		"""
		try:
			return self.current_date.isocalendar( ).week
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_week_number( self ) -> int'
			raise ex
	
	def fiscal_week_number( self ) -> int:
		"""Return the one-based fiscal-week number for the current date.

		Purpose:
			Calculates seven-day fiscal periods beginning on the represented fiscal-year start
			date.
			Dates before the fiscal year return zero and dates after the fiscal year return the
			final
			fiscal-week number.

		Returns:
			int: One-based fiscal-week number, or zero before the represented fiscal year.

		Raises:
			Error: Fiscal-year boundaries are unavailable or the week number cannot be calculated.
		"""
		try:
			if self.current_date < self.start_date:
				return 0
			calculation_date = min( self.current_date, self.end_date )
			return ((calculation_date - self.start_date).days // 7) + 1
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_week_number( self ) -> int'
			raise ex
	
	def fiscal_week_bounds( self, fiscal_week: int ) -> Tuple[ date, date ]:
		"""Return the boundaries of a one-based fiscal week.

		Purpose:
			Returns a seven-day period measured from the fiscal-year start date. The final week is
			truncated at the represented fiscal-year end date.

		Args:
			fiscal_week (int): One-based fiscal-week number.

		Returns:
			Tuple[date, date]: Inclusive first and final dates of the selected fiscal week.

		Raises:
			Error: The fiscal-week number is outside the represented fiscal year or cannot be
				resolved.
		"""
		try:
			throw_if( 'fiscal_week', fiscal_week )
			self.requested_fiscal_week = fiscal_week
			if self.requested_fiscal_week < 1:
				raise ValueError( 'Fiscal week must be greater than zero.' )
			week_start = self.start_date + timedelta( days=(self.requested_fiscal_week - 1) * 7 )
			if week_start > self.end_date:
				raise ValueError( 'Fiscal week exceeds the represented fiscal year.' )
			week_end = min( week_start + timedelta( days=6 ), self.end_date )
			return week_start, week_end
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_week_bounds( self, fiscal_week: int ) -> Tuple[ date, date ]'
			raise ex
	
	def current_weekday_name( self ) -> str:
		"""Return the weekday name for the current date.

		Purpose:
			Returns the full English weekday name associated with the current calculation date.

		Returns:
			str: Full weekday name.

		Raises:
			Error: The current date is unavailable or the weekday name cannot be resolved.
		"""
		try:
			return calendar.day_name[ self.current_date.weekday( ) ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'current_weekday_name( self ) -> str'
			raise ex
	
	def fiscal_month_name( self, fiscal_month: int ) -> str:
		"""Return the calendar-month name for a federal fiscal month.

		Purpose:
			Maps a federal fiscal-month number to its full English calendar-month name.

		Args:
			fiscal_month (int): Federal fiscal-month number from 1 through 12.

		Returns:
			str: Full calendar-month name.

		Raises:
			Error: The fiscal-month number is invalid or the month name cannot be resolved.
		"""
		try:
			month_start, _ = self.fiscal_month_bounds( fiscal_month )
			return calendar.month_name[ month_start.month ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_month_name( self, fiscal_month: int ) -> str'
			raise ex
	
	def calendar_month_name( self ) -> str:
		"""Return the calendar-month name for the current date.

		Purpose:
			Returns the full English calendar-month name associated with the current calculation
			date.

		Returns:
			str: Full calendar-month name.

		Raises:
			Error: The current date is unavailable or the month name cannot be resolved.
		"""
		try:
			return calendar.month_name[ self.current_date.month ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'calendar_month_name( self ) -> str'
			raise ex
	
	def fiscal_dates( self ) -> List[ date ]:
		"""Return every date in the represented fiscal year.

		Purpose:
			Builds an inclusive chronological sequence from the represented fiscal-year start date
			through its end date.

		Returns:
			List[date]: Ordered fiscal-year date sequence.

		Raises:
			Error: Fiscal-year boundaries are unavailable or the date sequence cannot be created.
		"""
		try:
			return [ self.start_date + timedelta( days=offset ) for offset in
				range( self.fiscal_days_in_year( ) ) ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_dates( self ) -> List[ date ]'
			raise ex
	
	def fiscal_weekdays( self ) -> List[ date ]:
		"""Return every weekday in the represented fiscal year.

		Purpose:
			Returns all Monday-through-Friday dates in the represented fiscal year without
			excluding
			federal holidays.

		Returns:
			List[date]: Ordered weekday dates.

		Raises:
			Error: The fiscal-year date sequence cannot be created or filtered.
		"""
		try:
			return [ current for current in self.fiscal_dates( ) if current.weekday( ) < 5 ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_weekdays( self ) -> List[ date ]'
			raise ex
	
	def fiscal_weekends( self ) -> List[ date ]:
		"""Return every weekend date in the represented fiscal year.

		Purpose:
			Returns all Saturday and Sunday dates in the represented fiscal year.

		Returns:
			List[date]: Ordered weekend dates.

		Raises:
			Error: The fiscal-year date sequence cannot be created or filtered.
		"""
		try:
			return [ current for current in self.fiscal_dates( ) if current.weekday( ) >= 5 ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_weekends( self ) -> List[ date ]'
			raise ex
	
	def fiscal_workdays( self, use_observed: bool = True ) -> List[ date ]:
		"""Return every workday in the represented fiscal year.

		Purpose:
			Returns all Monday-through-Friday dates after excluding either observed or actual
			federal
			holiday dates.

		Args:
			use_observed (bool): Uses observed holiday dates when ``True`` and actual dates when
				``False``.

		Returns:
			List[date]: Ordered workday dates.

		Raises:
			Error: Fiscal-year dates or federal-holiday dates cannot be created.
		"""
		try:
			self.use_observed = use_observed
			federal_holiday = FederalHoliday( self.fiscal_year )
			key = 'observed' if self.use_observed else 'actual'
			holiday_dates = { payload[ key ] for payload in federal_holiday.holidays( ).values( ) }
			return [ current for current in self.fiscal_dates( ) if
				current.weekday( ) < 5 and current not in holiday_dates ]
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_workdays( self, use_observed: bool = True ) -> List[ date ]'
			raise ex
	
	def fiscal_calendar( self ) -> Dict[ str, List[ date ] ]:
		"""Return fiscal-year dates grouped by month name.

		Purpose:
			Builds an ordered mapping of the twelve federal fiscal months to their inclusive date
			sequences.

		Returns:
			Dict[str, List[date]]: Month names mapped to ordered dates within each fiscal month.

		Raises:
			Error: Fiscal-month boundaries or date sequences cannot be created.
		"""
		try:
			result: Dict[ str, List[ date ] ] = { }
			for fiscal_month in range( 1, 13 ):
				month_name = self.fiscal_month_name( fiscal_month )
				month_start, month_end = self.fiscal_month_bounds( fiscal_month )
				month_days = (month_end - month_start).days + 1
				result[ month_name ] = [ month_start + timedelta( days=offset ) for offset in
					range( month_days ) ]
			return result
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'fiscal_calendar( self ) -> Dict[ str, List[ date ] ]'
			raise ex
	
	def fiscal_month_dates( self, fiscal_month: int ) -> List[ List[ date ] ]:
		"""Return complete date rows for a federal fiscal month."""
		return self.fiscal_month_calendar( fiscal_month )
	
	def fiscal_month_day_numbers( self, fiscal_month: int ) -> List[ List[ int ] ]:
		"""Return day-number rows for a federal fiscal month."""
		return self.fiscal_month_weeks( fiscal_month )
	
	def dates_by_month( self ) -> Dict[ str, List[ date ] ]:
		"""Return fiscal-year dates grouped by month name."""
		return self.fiscal_calendar( )
	
	def weekdays_by_month( self ) -> Dict[ str, int ]:
		"""Return weekday counts grouped by federal fiscal month.

		Purpose:
			Returns Monday-through-Friday counts for each fiscal month without excluding federal
			holidays.

		Returns:
			Dict[str, int]: Fiscal-month names mapped to weekday counts.

		Raises:
			Error: A fiscal-month weekday count cannot be calculated.
		"""
		try:
			return { self.fiscal_month_name( fiscal_month ): self.weekdays_in_month( fiscal_month )
				for fiscal_month in range( 1, 13 ) }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'weekdays_by_month( self ) -> Dict[ str, int ]'
			raise ex
	
	def weekends_by_month( self ) -> Dict[ str, int ]:
		"""Return weekend-day counts grouped by federal fiscal month.

		Purpose:
			Returns Saturday and Sunday counts for each month in the represented fiscal year.

		Returns:
			Dict[str, int]: Fiscal-month names mapped to weekend-day counts.

		Raises:
			Error: A fiscal-month weekend count cannot be calculated.
		"""
		try:
			return { self.fiscal_month_name( fiscal_month ): self.weekends_in_month( fiscal_month )
				for fiscal_month in range( 1, 13 ) }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'weekends_by_month( self ) -> Dict[ str, int ]'
			raise ex
	
	def workdays_by_month( self, use_observed: bool = True ) -> Dict[ str, int ]:
		"""Return workday counts grouped by federal fiscal month.

		Purpose:
			Returns Monday-through-Friday counts after excluding observed or actual federal
			holidays for each month in the represented fiscal year.

		Args:
			use_observed (bool): Excludes observed holiday dates when ``True`` and actual dates
				when ``False``.

		Returns:
			Dict[str, int]: Fiscal-month names mapped to workday counts.

		Raises:
			Error: A fiscal-month workday count cannot be calculated.
		"""
		try:
			self.use_observed = use_observed
			result: Dict[ str, int ] = { }
			for fiscal_month in range( 1, 13 ):
				month_name = self.fiscal_month_name( fiscal_month )
				month_start, month_end = self.fiscal_month_bounds( fiscal_month )
				result[ month_name ] = self.count_workdays( month_start, month_end,
					self.use_observed )
			return result
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'workdays_by_month( self, use_observed: bool = True ) -> Dict[ str, int ]'
			raise ex
	
	def holidays_by_month( self, use_observed: bool = True ) -> Dict[ str, List[ date ] ]:
		"""Return federal-holiday dates grouped by fiscal month.

		Purpose:
			Groups observed or actual federal-holiday dates by calendar-month name within the
			represented fiscal year. Months without holidays are included with empty lists.

		Args:
			use_observed (bool): Returns observed holiday dates when ``True`` and actual dates when
				``False``.

		Returns:
			Dict[str, List[date]]: Fiscal-month names mapped to ordered holiday dates.

		Raises:
			Error: Federal-holiday dates cannot be loaded or grouped.
		"""
		try:
			self.use_observed = use_observed
			result = { self.fiscal_month_name( fiscal_month ): [ ] for fiscal_month in
				range( 1, 13 ) }
			federal_holiday = FederalHoliday( self.fiscal_year )
			key = 'observed' if self.use_observed else 'actual'
			for payload in federal_holiday.holidays( ).values( ):
				holiday_date = payload[ key ]
				if self.start_date <= holiday_date <= self.end_date:
					result[ calendar.month_name[ holiday_date.month ] ].append( holiday_date )
			for month_name in result:
				result[ month_name ].sort( )
			return result
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('holidays_by_month( self, use_observed: bool = True ) -> '
			             'Dict[ str, List[ date ] ]')
			raise ex
	
	def holiday_dates_between( self, start: date | datetime, end: date | datetime,
		use_observed: bool = True ) -> Dict[ str, date ]:
		"""Return federal holiday names and date values within an inclusive range."""
		try:
			range_start, range_end = self._fiscal_range( start, end )
			self.range_start = range_start
			self.range_end = range_end
			self.use_observed = use_observed
			federal_holiday = FederalHoliday( self.fiscal_year )
			key = 'observed' if use_observed else 'actual'
			matches = [ (name, payload[ key ]) for name, payload in
				federal_holiday.holidays( ).items( ) if range_start <= payload[ key ] <=
				                                        range_end ]
			matches.sort( key=lambda item: item[ 1 ] )
			return { name: holiday_date for name, holiday_date in matches }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('holiday_dates_between( self, start: date | datetime, end: date | '
			             'datetime, use_observed: bool = True ) -> Dict[ str, date ]')
			raise ex
	
	def holidays_between( self, start: date | datetime, end: date | datetime,
		use_observed: bool = True ) -> Dict[ str, str ]:
		"""Return federal holiday names and ISO dates within an inclusive range.

		Purpose:
			Preserves the existing string-based return contract. Use ``holiday_dates_between`` for
			date values.
		"""
		try:
			return { name: holiday_date.isoformat( ) for name, holiday_date in
				self.holiday_dates_between( start, end, use_observed ).items( ) }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = ('holidays_between( self, start: date | datetime, end: date | datetime, '
			             'use_observed: bool = True ) -> Dict[ str, str ]')
			raise ex
	
	def holidays_remaining( self, use_observed: bool = True ) -> int:
		"""Return the remaining federal-holiday count in the represented fiscal year.

		Purpose:
			Counts observed or actual federal holidays from the current date through the
			represented
			fiscal-year end date. Future fiscal years begin counting at their fiscal-year start
			date;
			completed fiscal years return zero.

		Args:
			use_observed (bool): Counts observed holiday dates when ``True`` and actual dates when
				``False``.

		Returns:
			int: Inclusive number of remaining federal holidays.

		Raises:
			Error: Fiscal-year boundaries or federal-holiday dates cannot be evaluated.
		"""
		try:
			if self.current_date > self.end_date:
				return 0
			range_start = max( self.current_date, self.start_date )
			return self.count_holidays( range_start, self.end_date, use_observed )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'holidays_remaining( self, use_observed: bool = True ) -> int'
			raise ex
	
	def workdays_remaining( self, use_observed: bool = True ) -> int:
		"""Return the remaining workday count in the represented fiscal year.

		Purpose:
			Counts Monday-through-Friday dates from the current date through the represented
			fiscal-year end date after excluding observed or actual federal holidays. Future fiscal
			years begin counting at their fiscal-year start date; completed fiscal years return
			zero.

		Args:
			use_observed (bool): Excludes observed holiday dates when ``True`` and actual dates
				when ``False``.

		Returns:
			int: Inclusive number of remaining workdays.

		Raises:
			Error: Fiscal-year boundaries or workday dates cannot be evaluated.
		"""
		try:
			if self.current_date > self.end_date:
				return 0
			range_start = max( self.current_date, self.start_date )
			return self.count_workdays( range_start, self.end_date, use_observed )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'workdays_remaining( self, use_observed: bool = True ) -> int'
			raise ex
	
	def weekends_remaining( self ) -> int:
		"""Return the remaining weekend-day count in the represented fiscal year.

		Purpose:
			Counts Saturday and Sunday dates from the current date through the represented
			fiscal-year
			end date. Future fiscal years begin counting at their fiscal-year start date; completed
			fiscal years return zero.

		Returns:
			int: Inclusive number of remaining weekend dates.

		Raises:
			Error: Fiscal-year boundaries or weekend dates cannot be evaluated.
		"""
		try:
			if self.current_date > self.end_date:
				return 0
			range_start = max( self.current_date, self.start_date )
			return self.count_weekends( range_start, self.end_date )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'weekends_remaining( self ) -> int'
			raise ex
	
	def to_dict( self ) -> Dict[ str, object ]:
		"""Return the mapped fiscal-year row as a dictionary.

		Purpose:
			Return the mapped fiscal-year row as a dictionary.

		Returns:
			Dict[str, object]: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return { 'FiscalYear': self.fiscal_year, 'BPOA': self.bpoa, 'EPOA': self.epoa,
				'StartDate': self.start_date, 'EndDate': self.end_date,
				'ExpirationDate': self.expiration_date, 'CancellationDate': self.cancellation_date,
				'Weekdays': self.weekdays, 'Weekends': self.weekends, 'Workdays': self.workdays,
				'CompensableDays': self.compensable_days,
				'CompensableHours': self.compensable_hours, 'Type': self.type,
				'Availability': self.availability, }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FiscalYear'
			ex.method = 'to_dict( self ) -> Dict[ str, object ]'
			raise ex

class FederalHoliday( DB ):
	"""Federal-holiday database entity.

	Purpose:
		Maps one ``FederalHolidays`` database row to typed properties and provides actual-date,
		observed-date, holiday-membership, weekend, and dictionary-export operations.

	Attributes:
		input_fiscal_year (str): Fiscal year supplied to the constructor.
		actual_date (date): Holiday date assigned by ``observed_date``.
		when (date | None): Normalized date assigned by holiday and weekend tests.
		use_observed (bool): Indicates whether holiday tests use observed dates.
		id (int): Read-only database row identifier.
		fiscal_year (str): Read-only fiscal-year identifier.
		columbus_day (date): Read-only Columbus Day date.
		veterans_day (date): Read-only Veterans Day date.
		thanksgiving_day (date): Read-only Thanksgiving Day date.
		christmas_day (date): Read-only Christmas Day date.
		new_years_day (date): Read-only New Year's Day date.
		martin_luther_king_day (date): Read-only Martin Luther King Jr. Day date.
		presidents_day (date): Read-only Presidents Day date.
		memorial_day (date): Read-only Memorial Day date.
		juneteenth_day (date): Read-only Juneteenth National Independence Day date.
		independence_day (date): Read-only Independence Day date.
		labor_day (date): Read-only Labor Day date.
		"""
	
	id: int
	fiscal_year: str
	columbus_day: date
	veterans_day: date
	thanksgiving_day: date
	christmas_day: date
	new_years_day: date
	martin_luther_king_day: date
	presidents_day: date
	memorial_day: date
	juneteenth_day: date
	independence_day: date
	labor_day: date
	input_fiscal_year: str
	actual_date: date
	when: date
	use_observed: bool
	
	def __init__( self, fiscal_year: str | int ) -> None:
		"""Initialize a federal-holiday entity.

		Purpose:
			Validates the fiscal year, assigns query state, retrieves exactly one
			``FederalHolidays`` row,
			and maps each database column to its typed storage member.

		Args:
			fiscal_year (str): Fiscal year whose federal-holiday row is loaded.

		Returns:
			None: Initialization does not return a value.

		Raises:
			ValueError: ``fiscal_year`` is empty or a retrieved value cannot be converted.
			Error: Table validation or database retrieval fails.
			IndexError: The configured federal-holiday table is unavailable.
			KeyError: A required database column is missing.
			TypeError: A retrieved value has an unsupported type."""
		super( ).__init__( )
		throw_if( 'fiscal_year', fiscal_year )
		self.input_fiscal_year = str( fiscal_year )
		self.name = self.tables[ 1 ]
		df = self.query_holiday( self.name, self.input_fiscal_year )
		row = df.iloc[ 0 ]
		self.id = int( row[ 'ID' ] )
		self.fiscal_year = str( row[ 'FiscalYear' ] )
		self.columbus_day = to_date( row[ 'ColumbusDay' ] )
		self.veterans_day = to_date( row[ 'VeteransDay' ] )
		self.thanksgiving_day = to_date( row[ 'ThanksgivingDay' ] )
		self.christmas_day = to_date( row[ 'ChristmasDay' ] )
		self.new_years_day = to_date( row[ 'NewYearsDay' ] )
		self.martin_luther_king_day = to_date( row[ 'MartinLutherKingDay' ] )
		self.presidents_day = to_date( row[ 'PresidentsDay' ] )
		self.memorial_day = to_date( row[ 'MemorialDay' ] )
		self.juneteenth_day = to_date( row[ 'JuneteenthDay' ] )
		self.independence_day = to_date( row[ 'IndependenceDay' ] )
		self.labor_day = to_date( row[ 'LaborDay' ] )
	
	def __repr__( self ) -> str:
		"""Return the fiscal-year identifier.

		Purpose:
			Return the fiscal-year identifier.

		Returns:
			str: Value produced by the operation."""
		return self.fiscal_year
	
	def __dir__( self ) -> List[ str ]:
		"""Return public federal-holiday members.

		Purpose:
			Return public federal-holiday members.

		Returns:
			List[str]: Value produced by the operation."""
		return [ 'id', 'fiscal_year', 'columbus_day', 'veterans_day', 'thanksgiving_day',
			'christmas_day', 'new_years_day', 'martin_luther_king_day', 'presidents_day',
			'memorial_day', 'juneteenth_day', 'independence_day', 'labor_day', 'observed_date',
			'holidays', 'is_holiday', 'is_weekend', 'to_dict' ]
	
	def observed_date( self, value: date ) -> date:
		"""Return the observed date for a holiday.

		Purpose:
			Return the observed date for a holiday.

		Args:
			value (date): Value used by the operation.

		Returns:
			date: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'value', value )
			self.actual_date = value
			if self.actual_date.weekday( ) == 5:
				return self.actual_date - timedelta( days=1 )
			if self.actual_date.weekday( ) == 6:
				return self.actual_date + timedelta( days=1 )
			return self.actual_date
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FederalHoliday'
			ex.method = 'observed_date( self, value: date ) -> date'
			raise ex
	
	def holidays( self ) -> Dict[ str, Dict[ str, date ] ]:
		"""Return actual and observed federal-holiday dates.

		Purpose:
			Return actual and observed federal-holiday dates.

		Returns:
			Dict[str, Dict[str, date]]: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			actual_dates = { 'Columbus Day': self.columbus_day, 'Veterans Day': self.veterans_day,
				'Thanksgiving Day': self.thanksgiving_day, 'Christmas Day': self.christmas_day,
				"New Year's Day": self.new_years_day,
				'Birthday of Martin Luther King, Jr.': self.martin_luther_king_day,
				"Washington's Birthday": self.presidents_day, 'Memorial Day': self.memorial_day,
				'Juneteenth National Independence Day': self.juneteenth_day,
				'Independence Day': self.independence_day, 'Labor Day': self.labor_day, }
			return { name: { 'actual': actual, 'observed': self.observed_date( actual ) } for
				name, actual in actual_dates.items( ) }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FederalHoliday'
			ex.method = 'holidays( self ) -> Dict[ str, Dict[ str, date ] ]'
			raise ex
	
	def is_holiday( self, when: date | datetime, observed: bool = True ) -> bool:
		"""Determine whether a date is a federal holiday.

		Purpose:
			Determine whether a date is a federal holiday.

		Args:
			when (date | datetime): Value used by the operation.
			observed (bool): Value used by the operation.

		Returns:
			bool: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'when', when )
			self.when = to_date( when )
			self.use_observed = observed
			key = 'observed' if self.use_observed else 'actual'
			return any( self.when == payload[ key ] for payload in self.holidays( ).values( ) )
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FederalHoliday'
			ex.method = 'is_holiday( self, when: date | datetime, observed: bool = True ) -> bool'
			raise ex
	
	def is_weekend( self, when: date | datetime ) -> bool:
		"""Determine whether a date falls on a weekend.

		Purpose:
			Determine whether a date falls on a weekend.

		Args:
			when (date | datetime): Value used by the operation.

		Returns:
			bool: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			throw_if( 'when', when )
			self.when = to_date( when )
			return self.when.weekday( ) >= 5
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FederalHoliday'
			ex.method = 'is_weekend( self, when: date | datetime ) -> bool'
			raise ex
	
	def to_dict( self ) -> Dict[ str, object ]:
		"""Return the mapped federal-holiday row as a dictionary.

		Purpose:
			Return the mapped federal-holiday row as a dictionary.

		Returns:
			Dict[str, object]: Value produced by the operation.

		Raises:
			Error: The operation fails and the underlying exception is wrapped."""
		try:
			return { 'ID': self.id, 'FiscalYear': self.fiscal_year,
				'ColumbusDay': self.columbus_day, 'VeteransDay': self.veterans_day,
				'ThanksgivingDay': self.thanksgiving_day, 'ChristmasDay': self.christmas_day,
				'NewYearsDay': self.new_years_day,
				'MartinLutherKingDay': self.martin_luther_king_day,
				'PresidentsDay': self.presidents_day, 'MemorialDay': self.memorial_day,
				'JuneteenthDay': self.juneteenth_day, 'IndependenceDay': self.independence_day,
				'LaborDay': self.labor_day, }
		except Exception as e:
			ex = Error( e )
			ex.module = 'fiscal'
			ex.cause = 'FederalHoliday'
			ex.method = 'to_dict( self ) -> Dict[ str, object ]'
			raise ex
