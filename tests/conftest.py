import pytest

from userharbor_inmemory import InMemoryUserStore


@pytest.fixture
def user_store() -> InMemoryUserStore:
    return InMemoryUserStore()
