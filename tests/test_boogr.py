"""Tests for Fiscal's bundled diagnostic helpers."""

from fiscal import config
from fiscal.boogr import Error, get_config_bool, sanitize_text


def test_nonboolean_configuration_uses_default( monkeypatch ) -> None:
	"""Verify string-like configuration values are not coerced to true."""
	monkeypatch.setattr( config, 'TEST_BOOLEAN', 'false', raising=False )

	assert get_config_bool( 'TEST_BOOLEAN', True ) is True
	assert get_config_bool( 'TEST_BOOLEAN', False ) is False


def test_error_metadata_is_sanitized_once( ) -> None:
	"""Verify constructor and later metadata assignments preserve useful safe text."""
	error = Error( ValueError( 'Invalid value from user@example.com' ), cause='Parser' )
	error.method = 'parse_file( path=/workspace/private/input.csv )'

	assert '[EMAIL]' in error.message
	assert '[PATH]' in error.method
	assert error.cause == 'Parser'


def test_secret_text_is_masked( ) -> None:
	"""Verify common credential labels are redacted before logging."""
	assert sanitize_text( 'api_key=super-secret' ) == 'api_key=[SECRET]'
