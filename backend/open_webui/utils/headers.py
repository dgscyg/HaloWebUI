from __future__ import annotations

from urllib.parse import quote

from open_webui.env import ENABLE_FORWARD_USER_INFO_HEADERS


def include_user_info_headers(headers: dict[str, str], user) -> dict[str, str]:
    if not ENABLE_FORWARD_USER_INFO_HEADERS or user is None:
        return headers

    return {
        **headers,
        "X-OpenWebUI-User-Name": quote(str(getattr(user, "name", "")), safe=" "),
        "X-OpenWebUI-User-Id": str(getattr(user, "id", "")),
        "X-OpenWebUI-User-Email": str(getattr(user, "email", "")),
        "X-OpenWebUI-User-Role": str(getattr(user, "role", "")),
    }
