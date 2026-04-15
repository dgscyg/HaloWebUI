from open_webui.utils.data_management import deep_merge_dict, get_database_restore_support


def test_deep_merge_dict_recursively_merges_nested_objects():
    current = {
        "auth": {"signup": True, "providers": {"google": True, "github": False}},
        "features": {"web_search": True},
    }
    patch = {
        "auth": {"providers": {"github": True}},
        "features": {"images": True},
    }

    merged = deep_merge_dict(current, patch)

    assert merged == {
        "auth": {"signup": True, "providers": {"google": True, "github": True}},
        "features": {"web_search": True, "images": True},
    }


def test_get_database_restore_support_reports_expected_reason():
    assert get_database_restore_support("sqlite", 1) == {
        "backend": "sqlite",
        "worker_count": 1,
        "supported": True,
        "reason": None,
    }
    assert get_database_restore_support("postgresql", 1)["reason"] == "backend_not_sqlite"
    assert get_database_restore_support("sqlite", 2)["reason"] == "multiple_workers_not_supported"
