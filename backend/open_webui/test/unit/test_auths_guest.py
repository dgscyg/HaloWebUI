import pathlib
import sys

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[3]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def test_guest_group_lookup_uses_direct_group_name_query(monkeypatch):
    from open_webui.routers import auths as auths_router

    sentinel = object()
    calls = {}

    def fake_get_group_by_name(name: str):
        calls["group_name"] = name
        return sentinel

    def fail_get_groups():
        raise AssertionError("guest group lookup should not scan all groups")

    monkeypatch.setattr(
        auths_router.Groups,
        "get_group_by_name",
        fake_get_group_by_name,
    )
    monkeypatch.setattr(auths_router.Groups, "get_groups", fail_get_groups)

    assert auths_router._get_group_by_name("Guest") is sentinel
    assert calls == {"group_name": "Guest"}
