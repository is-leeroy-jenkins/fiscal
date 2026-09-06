# Development

## Environment

```bash
python -m venv .venv
```

Activate the environment and install project requirements:

```bash
pip install -e ".[dev]"
```

## Format Source

```bash
black fiscal tests
```

## Validate Python

```bash
python -m compileall -q fiscal
```

## Build Documentation

```bash
mkdocs build --strict
```

## Preview Documentation

```bash
mkdocs serve
```

Open the local address shown by MkDocs, normally `http://127.0.0.1:8000/`.

## Test Coverage

Run the automated suite:

```bash
pytest
```

The suite covers:

- constructors and database queries
- every public method
- all twelve fiscal months
- all four fiscal quarters
- valid and invalid fiscal weeks
- leap and non-leap years
- actual and observed holiday paths
- reversed and nonintersecting ranges
- text and HTML calendar rendering
- date ranges crossing calendar years
- OMB regular and pay-period FTE denominators
- every annual database denominator against a calendar-derived value
- partial-period compensable hours and holiday-adjusted work hours

## Publish a Release

The PyPI distribution is named `fiscal-pi`, while its import package remains `fiscal`. GitHub releases
invoke `.github/workflows/release.yml`, which builds the source and wheel distributions and publishes
them through PyPI Trusted Publishing.

Configure the PyPI publisher with:

- owner: `is-leeroy-jenkins`
- repository: `fiscal`
- workflow: `release.yml`
- environment: `pypi`

## Release Validation

Before release:

```bash
python -m compileall -q fiscal
pytest
mkdocs build --strict
```
