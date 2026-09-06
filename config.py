'''
  ******************************************************************************************
      Assembly:                fiscal
      Filename:                config.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="config.py" company="Terry D. Eppler">

	     config.py
	     Copyright ©  2020  Terry Eppler

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
    config.py
  </summary>
  ******************************************************************************************
'''
import os
import re
from typing import Optional, List, Dict
from pathlib import Path

# -------------- APP-LEVEL UTILITIES -------------

def throw_if( name: str, value: object ) -> None:
	"""Raise ``ValueError`` when a required value is empty.

	Purpose:
		Provides the configuration module's required-value guard. Python-falsy values—including
		``None``, ``False``, numeric zero, empty strings, and empty containers—are rejected with a
		message containing the caller-supplied setting name. This behavior is intentionally broader
		than the public guard in ``fiscal.__init__``.

	Args:
		name (str): Name of the argument or configuration value being validated.
		value (object): Value to validate.

	Returns:
		None: Successful validation has no return value or side effect.

	Raises:
		ValueError: Raised when ``value`` is falsy.
	"""
	if not value:
		raise ValueError( f'Argument "{name}" cannot be empty!' )

def get_bool( name: str, default: bool = False ) -> bool:
	"""Read a Boolean environment variable using the application's accepted true values.

	Purpose:
		Converts environment-variable text into a deterministic Boolean without raising during
		module initialization. Matching is case-insensitive and ignores surrounding whitespace.
		Missing variables return ``default``; defined values of ``1``, ``true``, ``yes``, ``y``, and
		``on`` return ``True``; every other defined value returns ``False``.

	Args:
		name (str): Environment variable name.
		default (bool): Default value used when the environment variable is not defined.

	Returns:
		bool: Parsed Boolean value. An invalid setting name or unexpected environment-access failure
			returns the original ``default``.
	"""
	try:
		throw_if( 'name', name )
		value = os.getenv( name )
		return default if value is None else value.strip( ).lower( ) in (
				'1',
				'true',
				'yes',
				'y',
				'on'
		)
	except Exception:
		return default

def get_int( name: str, default: int ) -> int:
	"""Read an integer environment variable with a deterministic fallback.

	Purpose:
		Parses an optional environment variable with Python's base-10 ``int`` conversion after
		removing surrounding whitespace. Missing, empty, whitespace-only, nonnumeric, or otherwise
		invalid values return ``default`` so configuration import remains deterministic.

	Args:
		name (str): Environment variable name.
		default (int): Default integer value used when parsing is not possible.

	Returns:
		int: Parsed integer value or the supplied default value.
	"""
	try:
		throw_if( 'name', name )
		value = os.getenv( name )
		return default if value in (None, '') else int( str( value ).strip( ) )
	except Exception:
		return default

def get_float( name: str, default: float ) -> float:
	"""Read a floating-point environment variable with a deterministic fallback.

	Purpose:
		Parses an optional environment variable with Python's ``float`` conversion after removing
		surrounding whitespace. Missing, empty, whitespace-only, nonnumeric, or otherwise invalid
		values return ``default`` so configuration import remains deterministic.

	Args:
		name (str): Environment variable name.
		default (float): Default floating-point value used when parsing is not possible.

	Returns:
		float: Parsed floating-point value or the supplied default value.
	"""
	try:
		throw_if( 'name', name )
		value = os.getenv( name )
		return default if value in (None, '') else float( str( value ).strip( ) )
	except Exception:
		return default

def get_path( name: str, default: Path ) -> Path:
	"""Read a path environment variable and return a resolved ``Path``.

	Purpose:
		Resolves optional filesystem configuration to an absolute ``Path``. A defined nonempty
		environment value is resolved relative to the process working directory; otherwise the
		default path is resolved. The function does not create the path or require it to exist.
		Invalid setting names and conversion failures fall back to the resolved default.

	Args:
		name (str): Environment variable name.
		default (Path): Default path used when the environment variable is not defined.

	Returns:
		Path: Absolute configured path or absolute fallback path. Existence is not guaranteed.
	"""
	try:
		throw_if( 'name', name )
		throw_if( 'default', default )
		value = os.getenv( name )
		return Path( value ).resolve( ) if value else default.resolve( )
	except Exception:
		return default.resolve( )

def get_text( name: str, default: str ) -> str:
	"""Read a text environment variable with a deterministic fallback.

	Purpose:
		Returns an environment variable as text without trimming or normalization. A missing value or
		an exact empty string uses ``default``; whitespace-only strings remain valid configured text.
		Invalid setting names and environment-access failures also fall back to ``default``.

	Args:
		name (str): Environment variable name.
		default (str): Default text value.

	Returns:
		str: Environment value or supplied default.
	"""
	try:
		throw_if( 'name', name )
		value = os.getenv( name )
		return default if value in (None, '') else str( value )
	except Exception:
		return default
	
# ----------------- CONSTANTS -------------------

TABLES = [ 'BudgetFiscalYears', 'FederalHolidays' ]
ROOT_DIR = Path( __file__ ).resolve( ).parent
DB_DIR: Path = get_path( 'DB_DIR', ROOT_DIR / 'sqlite' )
DB_PATH: str = get_text( 'DB_PATH', str( DB_DIR / 'data.db' ) )
