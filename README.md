<picture>
  <img src="https://github.com/userharbor/userharbor/raw/master/docs/assets/logo-full.png" alt="userharbor">
</picture>

[![GitHub License](https://img.shields.io/github/license/userharbor/userharbor-inmemory)](https://github.com/userharbor/userharbor-inmemory?tab=MIT-1-ov-file)
[![Tests](https://img.shields.io/github/actions/workflow/status/userharbor/userharbor-inmemory/tests.yml?label=tests)](https://github.com/userharbor/userharbor-inmemory/actions/workflows/tests.yml)
[![Codecov](https://img.shields.io/codecov/c/github/userharbor/userharbor-inmemory)](https://codecov.io/gh/userharbor/userharbor-inmemory)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/userharbor-inmemory)](https://pypi.org/project/userharbor-inmemory)
[![PyPI - Version](https://img.shields.io/pypi/v/userharbor-inmemory)](https://pypi.org/project/userharbor-inmemory)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Pytest](https://img.shields.io/badge/testing-Pytest-red?logo=pytest&logoColor=red)](https://docs.pytest.org/)

`userharbor-inmemory` is a minimal, contract-tested [`UserStore`](https://userharbor.github.io/userharbor/integrations/custom/) implementation for [UserHarbor](https://github.com/userharbor/userharbor). It can be installed directly for tests and examples or used as a GitHub template when building a custom storage integration.

> [!WARNING]
> All data is process-local and is lost when the store instance is discarded. This package is not a persistent database and is not intended for production storage.

## Installation

```bash
pip install userharbor-inmemory
```

The package depends on `userharbor` and has no database or framework dependencies.

## Usage

```python
from userharbor import UserHarbor
from userharbor_inmemory import InMemoryUserStore


store = InMemoryUserStore()

harbor = UserHarbor(
    secret_key="your-secret-key",
    store=store,
    email_sender=email_sender,
)
```

Each `InMemoryUserStore` instance starts empty and keeps its data for the lifetime of that instance.

The store implements the complete UserHarbor persistence contract:

* users and password hashes
* email verification and password reset tokens
* sessions and session refresh
* roles and permissions
* user-role and role-permission assignments
* commit, rollback, and nested transaction behavior

Each user has at most one active email verification token and one active password reset token. Storing a replacement invalidates the previous token. Users may have multiple active sessions.

## Use as an integration template

Select **Use this template** on GitHub and create a new repository. The generated repository starts with a complete implementation and a passing contract suite, so backend code can be replaced incrementally while the tests continue to verify `UserStore` behavior.

GitHub copies files without replacing project-specific names. After creating a repository:

1. Rename the distribution in `pyproject.toml`.
2. Rename the `userharbor_inmemory` package and `InMemoryUserStore` class.
3. Update project metadata, links, badges, and this README.
4. Replace the in-memory dictionaries and snapshot transaction with the target backend.
5. Adapt the `user_store` fixture in `tests/conftest.py` to create and clean up the backend.
6. Keep backend-specific tests separate from the shared contract suite.
7. Run the complete test suite before publishing.

The contract tests stay intentionally small in this repository:

```python
# tests/test_user_store_contract.py

from userharbor.testing.user_store_contract import *  # noqa: F403
```

```python
# tests/conftest.py

import pytest

from userharbor_inmemory import InMemoryUserStore


@pytest.fixture
def user_store() -> InMemoryUserStore:
    return InMemoryUserStore()
```

See the [UserStore contract testing guide](https://userharbor.github.io/userharbor/Development/contract-tests/) and [custom integrations guide](https://userharbor.github.io/userharbor/integrations/custom/) for the complete behavioral requirements.

## Development

Install the project and run its tests:

```bash
uv sync
uv run pytest
```

The suite imports the shared contract distributed with UserHarbor. Tests specific to this package remain in `tests/test_public_api.py`.

To develop against an unpublished local UserHarbor checkout, keep both repositories in the same parent directory and run:

```bash
uv run --with-editable ../userharbor pytest
```

## Limitations

`InMemoryUserStore` is deliberately small. It does not provide persistence across process restarts, cross-process sharing, durable transactions, or concurrency guarantees. Its snapshot-based transaction implementation exists to reproduce the atomic behavior required by UserHarbor in tests and examples.

## License

UserHarbor In-Memory is licensed under the MIT License. See [LICENSE](LICENSE) for details.
