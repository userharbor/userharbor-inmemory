def test_exports_in_memory_user_store() -> None:
    from userharbor_inmemory import InMemoryUserStore

    assert InMemoryUserStore is not None
