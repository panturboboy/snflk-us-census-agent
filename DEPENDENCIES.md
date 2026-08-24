# Dependency Management

This project uses pip-tools for locked, reproducible dependency management.

## Files

- **requirements.in** - Production dependencies (human-readable)
- **requirements.lock** - Pinned production dependencies (197 packages including transitive)
- **requirements-dev.in** - Development dependencies (human-readable)  
- **requirements-dev.lock** - Pinned development dependencies (270 packages including transitive)
- **pyproject.toml** - Package metadata and tool configurations

## Installation

### For Users (Production)
```bash
pip install -r requirements.lock
```

### For Developers
```bash
pip install -r requirements-dev.lock
```

Or with modern editable install:
```bash
pip install -e ".[dev]"
```

## Updating Dependencies

### Update a Specific Package
```bash
pip-compile requirements.in --upgrade-package <package-name>
pip-compile requirements-dev.in --upgrade-package <package-name>
```

### Update All Dependencies
```bash
pip-compile requirements.in --upgrade
pip-compile requirements-dev.in --upgrade
```

### Then Install Updated Versions
```bash
pip-sync requirements-dev.lock
```

## Dependency Structure

**Production (requirements.lock):**
- streamlit 1.40.0 (UI framework)
- pydantic 2.10.0+ (data validation)
- snowflake-connector-python 3.7.0+ (Snowflake client)
- snowflake-snowpark-python 1.11.0+ (Dataframe API)
- python-dotenv 1.0.0 (environment configuration)
- requests 2.31.0+ (HTTP client)
- ~30 transitive dependencies (altair, protobuf, cryptography, etc.)

**Development (requirements-dev.lock):**
- All production dependencies
- pytest 7.4.0+ (testing framework)
- pytest-cov 4.1.0+ (coverage reports)
- pytest-mock 3.11.1+ (mocking support)
- black 23.0.0+ (code formatting)
- isort 5.12.0+ (import sorting)
- flake8 6.0.0+ (linting)
- mypy 1.4.0+ (type checking)
- pre-commit 3.3.0+ (git hooks)
- ~80 transitive dependencies (ast-serialize, tomli, etc.)

## Why Lock Files

Lock files ensure:
- ✅ **Reproducibility:** Everyone uses the same versions
- ✅ **Consistency:** No "works on my machine" surprises
- ✅ **Security:** Deliberate updates vs accidental breaking changes
- ✅ **Traceability:** Version history in git
- ✅ **CI/CD:** Predictable builds in pipelines

## Best Practices

1. **Development:** Use `requirements-dev.lock` for local work
2. **Production:** Use `requirements.lock` for deployment
3. **Committing:** Always commit lock files when updating dependencies
4. **Reviewing:** Review lock file changes to catch dependency conflicts
5. **Updating:** Update regularly but deliberately, not reactively

## Troubleshooting

### Version Conflicts
If pip-compile can't resolve a version:
```bash
pip-compile requirements.in --verbose
```

This shows the resolution process and helps identify conflicts.

### Transitive Dependency Issues
Check what brought in an unwanted package:
```bash
pip show <package-name>
```

Then trace back to `requirements.in` or `requirements-dev.in`.

## Migration Path

This project migrated from simple `requirements.txt` to locked dependencies:

1. Created `requirements.in` from `requirements.txt`
2. Created `requirements-dev.in` for development tools
3. Generated `.lock` files with all transitive dependencies
4. Both `.in` files and `.lock` files are committed to git
5. Users and CI/CD use `.lock` files for deterministic installs

## Python Version

Lock files are generated for **Python 3.11+** (per `pyproject.toml`).

If using a different Python version, regenerate lock files:
```bash
pip-compile --python-version 3.12 requirements.in
```

---

**Last updated:** 2026-08-24  
**Total production packages:** 197  
**Total dev packages:** 270
