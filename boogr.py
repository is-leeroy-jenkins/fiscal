'''
  ******************************************************************************************
      Assembly:                Chonky
      Filename:                boogr.py
      Author:                  Terry D. Eppler
      Created:                 05-31-2022

      Last Modified By:        Terry D. Eppler
      Last Modified On:        05-01-2025
  ******************************************************************************************
  <copyright file="Chonky.py" company="Terry D. Eppler">

	 Chonky is a modular text-processing framework for machine-learning workflows based in python

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
    boogr.py
  </summary>
  ******************************************************************************************
  '''
from __future__ import annotations
import traceback
from sys import exc_info
from typing import List, Optional, Tuple
import FreeSimpleGUI as sg
import html

class Dark( ):
	"""FreeSimpleGUI dark-theme configuration.

	Purpose:
		Applies the application's ``DarkGrey15`` palette and global GUI options, then exposes the
		resolved colors, font, icon, scrollbar color, and default form size used by error dialogs.
		Construction changes FreeSimpleGUI process-wide theme, icon, font, and user-settings state;
		it does not merely hold immutable color constants.

	Attributes:
		theme_background (str | None): Active window background color.
		theme_textcolor (str | None): Active general text color.
		element_forecolor (str | None): Active element foreground color.
		element_backcolor (str | None): Active element background color.
		text_backcolor (str | None): Active text-element background color.
		text_forecolor (str | None): Active text-element foreground color.
		input_forecolor (str | None): Active input text color.
		input_backcolor (str | None): Active input background color.
		button_color (Tuple[str, str] | None): Active button foreground/background pair.
		icon_path (str | None): Relative path to the application window icon.
		theme_font (Tuple[str, int] | None): Global GUI font family and point size.
		scrollbar_color (str | None): Application scrollbar accent color.
		form_size (Tuple[int, int] | None): Default window dimensions in pixels.
	"""
	theme_background: Optional[ str ]
	theme_textcolor: Optional[ str ]
	element_forecolor: Optional[ str ]
	text_backcolor: Optional[ str ]
	text_forecolor: Optional[ str ]
	input_forecolor: Optional[ str ]
	input_backcolor: Optional[ str ]
	button_backcolor: Optional[ str ]
	button_forecolor: Optional[ str ]
	button_color: Optional[ Tuple[ str, str ] ]
	icon_path: Optional[ str ]
	theme_font: Optional[ Tuple[ str, int ] ]
	scrollbar_color: Optional[ str ]
	form_size: Optional[ Tuple[ int, int ] ]
	
	def __init__( self ):
		"""Apply and capture the application-wide dark theme.

		Purpose:
			Configures FreeSimpleGUI with ``DarkGrey15``, explicit text colors, the Tempus icon, and an
			11-point Roboto font. The resolved theme values are copied to instance members for reuse by
			dialog subclasses, and GUI user settings are saved under the ``Boo`` application key.

		Returns:
			None: Initialization operates through instance assignment and FreeSimpleGUI side effects.

		Raises:
			Exception: FreeSimpleGUI rejects a theme option, cannot load the icon, or cannot save user
				settings.
		"""
		sg.theme( 'DarkGrey15' )
		sg.theme_input_text_color( '#FFFFFF' )
		sg.theme_element_text_color( '#69B1EF' )
		sg.theme_text_color( '#69B1EF' )
		self.theme_background = sg.theme_background_color( )
		self.theme_textcolor = sg.theme_text_color( )
		self.element_forecolor = sg.theme_element_text_color( )
		self.element_backcolor = sg.theme_background_color( )
		self.text_backcolor = sg.theme_text_element_background_color( )
		self.text_forecolor = sg.theme_element_text_color( )
		self.input_forecolor = sg.theme_input_text_color( )
		self.input_backcolor = sg.theme_input_background_color( )
		self.button_backcolor = sg.theme_button_color_background( )
		self.button_forecolor = sg.theme_button_color_text( )
		self.button_color = sg.theme_button_color( )
		self.icon_path = r'resources\images\github\tempus.ico'
		self.theme_font = ('Roboto', 11)
		self.scrollbar_color = '#755600'
		self.form_size = (400, 200)
		sg.set_global_icon( icon=self.icon_path )
		sg.set_options( font=self.theme_font )
		sg.user_settings_save( 'Boo', r'\resources\theme' )
	
	def __dir__( self ) -> List[ str ] | None:
		"""List theme members intentionally exposed for interactive discovery.

		Purpose:
			Restricts ``dir(instance)`` to the color, font, icon, scrollbar, and form-size settings that
			constitute the supported theme interface.

		Returns:
			List[str] | None: Stable public theme-member names. The current implementation always returns
				a list.
		"""
		return [ 'form_size',
		         'theme_background',
		         'theme_textcolor',
		         'element_backcolor',
		         'element_forecolor',
		         'text_forecolor',
		         'text_backcolor',
		         'input_backcolor',
		         'input_forecolor',
		         'button_color',
		         'button_backcolor',
		         'button_forecolor',
		         'icon_path',
		         'theme_font',
		         'scrollbar_color' ]

class Error( Exception ):
	"""Exception wrapper carrying diagnostic and presentation metadata.

	Purpose:
		Captures an originating exception together with an optional heading, class/cause name, method
		signature, and module name. It snapshots the active exception type and formatted traceback at
		construction time so callers can either raise the wrapper or present it through
		``ErrorDialog`` without losing diagnostic context.

	Attributes:
		exception (Exception): Original exception supplied by the caller.
		heading (str | None): Optional user-facing error heading.
		cause (str | None): Optional class, component, or cause identifier.
		method (str | None): Optional method signature or operation name.
		module (str | None): Optional module identifier.
		type (type | None): Exception type active when the wrapper was constructed.
		trace (str): Formatted active traceback captured at construction time.
		info (str): Combined exception-type and traceback text returned by ``str``.
	"""
	
	def __init__( self, error: Exception, heading: str=None, cause: str=None,
			method: str=None, module: str=None ):
		"""Capture an exception and its current traceback context.

		Purpose:
			Stores the originating exception and optional display metadata, then snapshots
			``sys.exc_info`` and ``traceback.format_exc``. For a meaningful traceback, construct the
			wrapper inside the ``except`` block handling ``error``.

		Args:
			error (Exception): Original exception being wrapped.
			heading (str | None): Optional user-facing title for an error dialog.
			cause (str | None): Optional class, component, or cause identifier.
			method (str | None): Optional method signature or operation name.
			module (str | None): Optional module identifier.

		Returns:
			None: Initialization stores diagnostic state and does not return a value.
		"""
		super( ).__init__( )
		self.exception = error
		self.heading = heading
		self.cause = cause
		self.method = method
		self.module = module
		self.type = exc_info( )[ 0 ]
		self.trace = traceback.format_exc( )
		self.info = str( exc_info( )[ 0 ] ) + ': \r\n \r\n' + traceback.format_exc( )
	
	def __str__( self ) -> str | None:
		"""Return the captured exception type and traceback.

		Purpose:
			Provides the diagnostic ``info`` text used when the wrapper is logged, printed, or converted
			to a string. The text reflects the exception context captured during construction.

		Returns:
			str | None: Combined exception-type and formatted traceback text, or ``None`` if ``info`` was
				explicitly cleared after construction.
		"""
		if self.info is not None:
			return self.info
	
	def __dir__( self ) -> List[ str ] | None:
		"""List diagnostic members intended for interactive discovery.

		Purpose:
			Restricts ``dir(instance)`` to the public presentation and diagnostic names historically
			exposed by this wrapper.

		Returns:
			List[str] | None: Stable public diagnostic-member names. The current implementation always
				returns a list.
		"""
		return [ 'message',
		         'cause',
		         'method',
		         'module',
		         'scaler',
		         'stack_trace',
		         'info' ]

class ErrorDialog( Dark ):
	"""Modal FreeSimpleGUI presentation for a captured ``Error``.

	Purpose:
		Combines the application's dark theme with structured error metadata and renders a blocking
		dialog containing the heading, module, class/cause, method, and captured traceback. The dialog
		is created only when ``show`` is called; construction prepares theme and error state.

	Attributes:
		error (Error | None): Wrapped diagnostic object displayed by the dialog.
		heading (str | None): Optional user-facing heading copied from ``error``.
		module (str | None): Module identifier copied from ``error``.
		info (str | None): Formatted traceback copied from ``error.trace``.
		cause (str | None): Class, component, or cause identifier copied from ``error``.
		method (str | None): Method signature or operation name copied from ``error``.
	"""
	
	# Fields
	error: Optional[ Exception ]
	heading: Optional[ str ]
	module: Optional[ str ]
	info: Optional[ str ]
	cause: Optional[ str ]
	method: Optional[ str ]
	
	def __init__( self, error: Error ):
		"""Initialize theme and diagnostic state for an error dialog.

		Purpose:
			Applies the inherited dark theme, refreshes the dialog-specific global GUI options, sets the
			500-by-300-pixel form size, and copies presentation fields from the supplied ``Error``. GUI
			user settings are saved under the ``Mathy`` application key.

		Args:
			error (Error): Captured exception and metadata to present.

		Returns:
			None: Initialization assigns state and applies FreeSimpleGUI side effects.

		Raises:
			AttributeError: ``error`` does not provide the expected diagnostic members.
			Exception: FreeSimpleGUI theme, icon, option, or settings initialization fails.
		"""
		super( ).__init__( )
		sg.theme( 'DarkGrey15' )
		sg.theme_input_text_color( '#FFFFFF' )
		sg.theme_element_text_color( '#69B1EF' )
		sg.theme_text_color( '#69B1EF' )
		self.theme_background = sg.theme_background_color( )
		self.theme_textcolor = sg.theme_text_color( )
		self.element_forecolor = sg.theme_element_text_color( )
		self.element_backcolor = sg.theme_background_color( )
		self.text_backcolor = sg.theme_text_element_background_color( )
		self.text_forecolor = sg.theme_element_text_color( )
		self.input_forecolor = sg.theme_input_text_color( )
		self.input_backcolor = sg.theme_input_background_color( )
		self.button_backcolor = sg.theme_button_color_background( )
		self.button_forecolor = sg.theme_button_color_text( )
		self.button_color = sg.theme_button_color( )
		self.icon_path = r'resources\images\github\tempus.ico'
		self.theme_font = ('Roboto', 11)
		self.scrollbar_color = '#755600'
		sg.set_global_icon( icon=self.icon_path )
		sg.set_options( font=self.theme_font )
		sg.user_settings_save( 'Mathy', r'\resources\theme' )
		self.form_size = (500, 300)
		self.error = error
		self.heading = error.heading
		self.module = error.module
		self.info = error.trace
		self.cause = error.cause
		self.method = error.method
	
	def __str__( self ) -> str | None:
		"""Return the traceback text prepared for display.

		Purpose:
			Provides the copied ``Error.trace`` value when the dialog is logged, printed, or converted to
			a string. It does not open the GUI window.

		Returns:
			str | None: Captured formatted traceback, or ``None`` when no traceback text is assigned.
		"""
		return self.info
	
	def __dir__( self ) -> List[ str ] | None:
		"""List dialog members intentionally exposed for interactive discovery.

		Purpose:
			Restricts ``dir(instance)`` to dialog dimensions, theme settings, diagnostic fields, and the
			``show`` operation used by callers.

		Returns:
			List[str] | None: Stable public dialog-member names. The current implementation always
				returns a list.
		"""
		return [ 'size',
		         'settings_path',
		         'theme_background',
		         'theme_textcolor',
		         'element_backcolor',
		         'element_forecolor',
		         'text_forecolor',
		         'text_backcolor',
		         'input_backcolor',
		         'input_forecolor',
		         'button_color',
		         'button_backcolor',
		         'button_forecolor',
		         'icon_path',
		         'theme_font',
		         'scrollbar_color',
		         'progressbar_color',
		         'info',
		         'cause',
		         'method',
		         'error',
		         'heading',
		         'module',
		         'scaler',
		         'message' 'show' ]
	
	def show( self ) -> object:
		"""Display the blocking error dialog and close it after dismissal.

		Purpose:
			Builds a modal-style FreeSimpleGUI window containing the optional heading and a multiline
			diagnostic block with module, class/cause, method, and traceback information. The event loop
			continues until the user closes the window or activates the OK/Cancel controls, after which
			the window is closed.

		Returns:
			object: The method performs GUI side effects and currently returns ``None`` implicitly.

		Raises:
			Exception: FreeSimpleGUI cannot construct, read, or close the window.
		"""
		_msg = self.heading if isinstance( self.heading, str ) else None
		_info = f'Module:\t{self.module}\r\nClass:\t{self.cause}\r\n' \
		        f'Method:\t{self.method}\r\n \r\n{self.info}'
		_red = '#F70202'
		_font = ('Roboto', 10)
		_padsz = (3, 3)
		_layout = [ [ sg.Text( ) ],
		            [ sg.Text( f'{_msg}', size=(100, 1), key='-MSG-', text_color=_red, font=_font
		            ) ],
		            [ sg.Text( size=(150, 1) ) ],
		            [ sg.Multiline( f'{_info}', key='-INFO-', size=(80, 7), pad=_padsz ) ],
		            [ sg.Text( ) ],
		            [ sg.Text( size=(20, 1) ),
		              sg.Cancel( size=(15, 1), key='-CANCEL-' ),
		              sg.Text( size=(10, 1) ),
		              sg.Ok( size=(15, 1), key='-OK-' ) ] ]
		
		_window = sg.Window( r' Mathy', _layout,
			icon=self.icon_path,
			font=self.theme_font,
			size=self.form_size )
		
		while True:
			_event, _values = _window.read( )
			if _event in (sg.WIN_CLOSED, sg.WIN_X_EVENT, 'Canel', '-OK-'):
				break
		
		_window.close( )
