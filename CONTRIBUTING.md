# Contributing

## Local development

Install development dependencies:

```bash
python3 -m pip install -r requirements_common.txt
python3 -m pip install -r requirements_dev.txt
```

Start Home Assistant with this repository's `custom_components` directory on the Python path:

```bash
scripts/develop
```

## Checks

Run the focused checks before opening a change:

```bash
python3 -m compileall custom_components/tesla_fleet_schedule
python3 -m ruff check .
python3 -m ruff format . --check
```

Add and run tests with `pytest` when behavior changes.

## Release checklist

Confirm `custom_components/tesla_fleet_schedule/manifest.json`, `hacs.json`, README documentation, and tags/releases are aligned before publishing through HACS.

Choose a repository license before public distribution.