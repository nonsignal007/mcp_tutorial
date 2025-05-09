# Project Dependencies

## Runtime Dependencies
- Python 3.13.1
- httpx (for async HTTP client)
- pydantic (for type-safe configuration)

## Development Dependencies
- pytest 8.3.4
- pytest-cov 6.0.0
- pytest-asyncio 0.25.1

## Optional Dependencies
These dependencies are only needed for specific features:

### Testing
```
pip install -e ".[test]"
```

### Development
```
pip install -e ".[dev]"
```

## Version Management
Dependencies are managed through pyproject.toml and should be installed using a modern Python package manager like `uv` or `pip`.

### Installation
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .