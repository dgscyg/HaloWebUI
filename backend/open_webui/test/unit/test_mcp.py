import asyncio
import json
import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import patch


# Ensure `open_webui` is importable when running tests from repo root.
_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[3]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def test_mcp_streamable_http_client_json_and_sse():
    from aiohttp import web

    from open_webui.utils.mcp import MCPStreamableHttpClient

    seen_session_headers = []

    async def handler(request: web.Request):
        payload = await request.json()
        method = payload.get("method")

        # Record session header usage across requests.
        seen_session_headers.append(request.headers.get("Mcp-Session-Id"))

        if method == "initialize":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "result": {
                        "serverInfo": {"name": "TestMCP", "version": "0.0.1"},
                        "capabilities": {"tools": {}},
                    },
                },
                headers={"Mcp-Session-Id": "sess_123"},
            )

        if method == "notifications/initialized":
            # JSON-RPC notification: no response body required.
            return web.Response(status=200, headers={"Mcp-Session-Id": "sess_123"})

        if method == "tools/list":
            cursor = (payload.get("params") or {}).get("cursor")
            if not cursor:
                tools = [{"name": "foo/bar", "description": "t1", "inputSchema": {"type": "object"}}]
                result = {"tools": tools, "nextCursor": "c2"}
            else:
                tools = [{"name": "echo", "description": "t2", "inputSchema": {"type": "object"}}]
                result = {"tools": tools, "nextCursor": None}

            return web.json_response(
                {"jsonrpc": "2.0", "id": payload.get("id"), "result": result},
                headers={"Mcp-Session-Id": "sess_123"},
            )

        if method == "tools/call":
            # Return SSE to exercise the Streamable HTTP parsing branch.
            resp = web.StreamResponse(
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Mcp-Session-Id": "sess_123",
                },
            )
            await resp.prepare(request)

            msg = {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {
                    "content": [{"type": "text", "text": "ok"}],
                    "name": (payload.get("params") or {}).get("name"),
                    "arguments": (payload.get("params") or {}).get("arguments"),
                },
            }

            await resp.write(f"data: {json.dumps(msg)}\n\n".encode("utf-8"))
            await resp.write(b"data: [DONE]\n\n")
            await resp.write_eof()
            return resp

        return web.json_response(
            {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"message": "unknown method"}},
            status=400,
        )

    async def run():
        app = web.Application()
        app.router.add_post("/", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()

        # Determine the allocated port.
        port = site._server.sockets[0].getsockname()[1]
        url = f"http://127.0.0.1:{port}/"

        try:
            client = MCPStreamableHttpClient(url)
            init = await client.initialize()
            assert init.get("serverInfo", {}).get("name") == "TestMCP"

            await client.notify_initialized()
            tools = await client.list_tools()
            assert [t["name"] for t in tools] == ["foo/bar", "echo"]

            result = await client.call_tool("echo", {"x": 1})
            assert result.get("name") == "echo"
            assert result.get("arguments") == {"x": 1}
        finally:
            await runner.cleanup()

    asyncio.run(run())

    # First request (initialize) has no session id; subsequent ones should.
    assert seen_session_headers[0] in (None, "")
    assert any(h == "sess_123" for h in seen_session_headers[1:])


def test_get_tools_exposes_mcp_tool_and_routes_call(monkeypatch):
    # Avoid touching the tool DB layer.
    import open_webui.utils.tools as tools_mod

    monkeypatch.setattr(tools_mod.Tools, "get_tool_by_id", lambda _id: None)

    called = {}

    async def fake_execute_mcp_tool(connection, *, name, arguments, session_token=None, **_kwargs):
        called["connection"] = connection
        called["name"] = name
        called["arguments"] = arguments
        called["session_token"] = session_token
        return {"ok": True}

    monkeypatch.setattr(tools_mod, "execute_mcp_tool", fake_execute_mcp_tool)

    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                config=SimpleNamespace(
                    MCP_SERVER_CONNECTIONS=[{"url": "http://mcp.local", "auth_type": "none"}],
                    TOOL_SERVER_CONNECTIONS=[],
                ),
                MCP_SERVERS=[
                    {
                        "idx": 0,
                        "url": "http://mcp.local",
                        "server_info": {"name": "TestMCP"},
                        "tools": [
                            {
                                "name": "foo/bar",
                                "description": "desc",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"a": {"type": "string"}},
                                    "required": ["a"],
                                },
                            }
                        ],
                    }
                ],
                TOOL_SERVERS=[],
            )
        ),
        state=SimpleNamespace(token=SimpleNamespace(credentials="tok_abc")),
    )
    user = SimpleNamespace(id="u1", role="admin")

    tools = tools_mod.get_tools(request, ["mcp:0"], user, extra_params={})
    assert "mcp_0__foo_bar" in tools
    spec = tools["mcp_0__foo_bar"]["spec"]
    assert spec["name"] == "mcp_0__foo_bar"
    assert spec["parameters"]["type"] == "object"

    async def run():
        out = await tools["mcp_0__foo_bar"]["callable"](a="x")
        return out

    out = asyncio.run(run())
    assert out == {"ok": True}
    assert called["name"] == "foo/bar"
    assert called["arguments"] == {"a": "x"}
    assert called["session_token"] == "tok_abc"


def test_get_user_mcp_connections_normalize_apps_metadata():
    from open_webui.utils.user_tools import get_user_mcp_server_connections

    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(
                config=SimpleNamespace(
                    MCP_SERVER_CONNECTIONS=[
                        {
                            "url": "http://legacy.example",
                            "enabled": False,
                            "apps_enabled": "true",
                        }
                    ]
                )
            )
        )
    )
    user = SimpleNamespace(role="admin", settings=None)

    connections = get_user_mcp_server_connections(request, user)

    assert connections == [
        {
            "url": "http://legacy.example",
            "enabled": False,
            "apps_enabled": "true",
            "mcp_apps": {"ENABLE_MCP_APPS": True},
        }
    ]


def test_normalize_mcp_server_connection_preserves_legacy_apps_enabled_independent_from_base_enabled():
    from open_webui.utils.user_tools import normalize_mcp_server_connection

    connection = normalize_mcp_server_connection(
        {
            "url": "http://legacy.example",
            "enabled": False,
            "apps_enabled": True,
        }
    )

    assert connection == {
        "url": "http://legacy.example",
        "enabled": False,
        "apps_enabled": True,
        "mcp_apps": {"ENABLE_MCP_APPS": True},
    }


def test_set_mcp_servers_config_preserves_legacy_enabled_and_apps_state():
    from open_webui.routers.configs import MCPServerConnection, MCPServersConfigForm, set_mcp_servers_config

    user = SimpleNamespace(id="user-1")
    request = SimpleNamespace()

    saved = {}

    with patch("open_webui.routers.configs.set_user_mcp_server_connections") as setter:
        setter.side_effect = lambda _user, connections: saved.setdefault("connections", connections)
        form = MCPServersConfigForm(
            MCP_SERVER_CONNECTIONS=[
                MCPServerConnection(
                    url="http://mcp.local",
                    enabled=False,
                    mcp_apps={"ENABLE_MCP_APPS": True, "enabled": False},
                    server_info={"name": "Kept"},
                )
            ]
        )

        result = asyncio.run(set_mcp_servers_config(request, form, user))

    assert result == {
        "MCP_SERVER_CONNECTIONS": [
            {
                "url": "http://mcp.local",
                "enabled": False,
                "server_info": {"name": "Kept"},
                "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False},
            }
        ]
    }
    assert saved["connections"] == result["MCP_SERVER_CONNECTIONS"]


def test_set_mcp_servers_config_preserves_legacy_apps_enabled_without_collapsing_to_base_enabled():
    from open_webui.routers.configs import MCPServerConnection, MCPServersConfigForm, set_mcp_servers_config

    user = SimpleNamespace(id="user-1")
    request = SimpleNamespace()

    saved = {}

    with patch("open_webui.routers.configs.set_user_mcp_server_connections") as setter:
        setter.side_effect = lambda _user, connections: saved.setdefault("connections", connections)
        form = MCPServersConfigForm(
            MCP_SERVER_CONNECTIONS=[
                MCPServerConnection(
                    url="http://legacy.example",
                    enabled=False,
                    apps_enabled=True,
                )
            ]
        )

        result = asyncio.run(set_mcp_servers_config(request, form, user))

    assert result == {
        "MCP_SERVER_CONNECTIONS": [
            {
                "url": "http://legacy.example",
                "enabled": False,
                "apps_enabled": True,
            }
        ]
    }
    assert saved["connections"] == [
        {
            "url": "http://legacy.example",
            "enabled": False,
            "apps_enabled": True,
        }
    ]


def test_set_mcp_apps_config_updates_apps_flag_without_mutating_enabled_semantics():
    from open_webui.routers.configs import MCPAppsConfigForm, set_mcp_apps_config

    user = SimpleNamespace(id="user-1")
    request = SimpleNamespace()
    existing_connections = [
        {"url": "http://one.example", "enabled": False},
        {"url": "http://two.example", "config": {"enable": True}, "mcp_apps": {"enabled": True}},
    ]
    saved = {}

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=existing_connections,
    ), patch("open_webui.routers.configs.set_user_mcp_server_connections") as setter:
        setter.side_effect = lambda _user, connections: saved.setdefault("connections", connections)
        result = asyncio.run(
            set_mcp_apps_config(
                request,
                MCPAppsConfigForm(
                    ENABLE_MCP_APPS=True,
                    MCP_SERVER_APPS={"0": False, "1": True},
                ),
                user,
            )
        )

    assert result == {
        "ENABLE_MCP_APPS": True,
        "MCP_SERVER_APPS": {
            "0": False,
            "1": True,
        },
    }
    assert saved["connections"] == [
        {
            "url": "http://one.example",
            "enabled": False,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False},
        },
        {
            "url": "http://two.example",
            "config": {"enable": True},
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        },
    ]


def test_set_mcp_apps_config_preserves_legacy_apps_enabled_round_trip_when_base_disabled():
    from open_webui.routers.configs import MCPAppsConfigForm, set_mcp_apps_config

    user = SimpleNamespace(id="user-1")
    request = SimpleNamespace()
    existing_connections = [
        {"url": "http://legacy.example", "enabled": False, "apps_enabled": True},
    ]
    saved = {}

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=existing_connections,
    ), patch("open_webui.routers.configs.set_user_mcp_server_connections") as setter:
        setter.side_effect = lambda _user, connections: saved.setdefault("connections", connections)
        result = asyncio.run(
            set_mcp_apps_config(
                request,
                MCPAppsConfigForm(
                    ENABLE_MCP_APPS=True,
                    MCP_SERVER_APPS={"0": True},
                ),
                user,
            )
        )

    assert result == {
        "ENABLE_MCP_APPS": True,
        "MCP_SERVER_APPS": {
            "0": True,
        },
    }
    assert saved["connections"] == [
        {
            "url": "http://legacy.example",
            "enabled": False,
            "apps_enabled": True,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        }
    ]


def test_set_mcp_apps_config_preserves_mixed_server_apps_state_round_trip():
    from open_webui.routers.configs import MCPAppsConfigForm, set_mcp_apps_config

    user = SimpleNamespace(id="user-1")
    request = SimpleNamespace()
    existing_connections = [
        {"url": "http://one.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": False, "enabled": True}},
        {"url": "http://two.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False}},
        {"url": "http://three.example", "enabled": False, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
    ]
    saved = {}

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=existing_connections,
    ), patch("open_webui.routers.configs.set_user_mcp_server_connections") as setter:
        setter.side_effect = lambda _user, connections: saved.setdefault("connections", connections)
        result = asyncio.run(
            set_mcp_apps_config(
                request,
                MCPAppsConfigForm(
                    ENABLE_MCP_APPS=True,
                    MCP_SERVER_APPS={"0": True, "1": False, "2": True},
                ),
                user,
            )
        )

    assert result == {
        "ENABLE_MCP_APPS": True,
        "MCP_SERVER_APPS": {
            "0": True,
            "1": False,
            "2": True,
        },
    }
    assert saved["connections"] == [
        {
            "url": "http://one.example",
            "enabled": True,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        },
        {
            "url": "http://two.example",
            "enabled": True,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False},
        },
        {
            "url": "http://three.example",
            "enabled": False,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        },
    ]


def test_get_mcp_apps_config_reports_global_and_per_server_state():
    from open_webui.routers.configs import get_mcp_apps_config

    request = SimpleNamespace()
    user = SimpleNamespace(id="user-1")
    connections = [
        {"url": "http://one.example", "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
        {"url": "http://two.example", "enabled": False, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False}},
        {"url": "http://three.example", "mcp_apps": {"ENABLE_MCP_APPS": False, "enabled": True}},
    ]

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=connections,
    ):
        result = asyncio.run(get_mcp_apps_config(request, user))

    assert result == {
        "ENABLE_MCP_APPS": True,
        "MCP_SERVER_APPS": {
            "0": True,
            "1": False,
            "2": True,
        },
    }


def test_get_mcp_apps_config_preserves_stored_server_toggles_even_when_global_disabled():
    from open_webui.routers.configs import get_mcp_apps_config

    request = SimpleNamespace()
    user = SimpleNamespace(id="user-1")
    connections = [
        {"url": "http://one.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": False, "enabled": True}},
        {"url": "http://two.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": False, "enabled": False}},
        {"url": "http://three.example", "enabled": False, "mcp_apps": {"ENABLE_MCP_APPS": False, "enabled": True}},
    ]

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=connections,
    ):
        result = asyncio.run(get_mcp_apps_config(request, user))

    assert result == {
        "ENABLE_MCP_APPS": False,
        "MCP_SERVER_APPS": {
            "0": True,
            "1": False,
            "2": True,
        },
    }


def test_verify_mcp_server_connection_uses_session_token_for_session_auth():
    from open_webui.routers.configs import MCPServerConnection, verify_mcp_server_connection

    request = SimpleNamespace(state=SimpleNamespace(token=SimpleNamespace(credentials="sess-token")))
    user = SimpleNamespace(id="user-1")
    captured = {}

    async def fake_get_mcp_server_data(connection, *, session_token=None, **_kwargs):
        captured["connection"] = connection
        captured["session_token"] = session_token
        return {
            "server_info": {"name": "Session-backed"},
            "tools": [{"name": "echo", "description": "Echo"}],
        }

    with patch("open_webui.routers.configs.get_mcp_server_data", side_effect=fake_get_mcp_server_data):
        result = asyncio.run(
            verify_mcp_server_connection(
                request,
                MCPServerConnection(url="http://mcp.local", auth_type="session"),
                user,
            )
        )

    assert captured["session_token"] == "sess-token"
    assert captured["connection"]["auth_type"] == "session"
    assert result == {
        "server_info": {"name": "Session-backed"},
        "tool_count": 1,
        "tools": [{"name": "echo", "description": "Echo"}],
    }


def test_verify_mcp_server_connection_requires_authenticated_session_for_session_auth():
    from fastapi import HTTPException
    from open_webui.routers.configs import MCPServerConnection, verify_mcp_server_connection

    request = SimpleNamespace(state=SimpleNamespace())
    user = SimpleNamespace(id="user-1")

    with patch("open_webui.routers.configs.get_mcp_server_data") as get_mcp_server_data:
        try:
            asyncio.run(
                verify_mcp_server_connection(
                    request,
                    MCPServerConnection(url="http://mcp.local", auth_type="session"),
                    user,
                )
            )
            raise AssertionError("Expected HTTPException")
        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail == "Not authenticated"

    get_mcp_server_data.assert_not_called()


def test_get_mcp_apps_capabilities_exposes_stable_frontend_contract():
    from open_webui.routers.configs import get_mcp_apps_capabilities

    request = SimpleNamespace(state=SimpleNamespace(token=SimpleNamespace(credentials="tok_abc")))
    user = SimpleNamespace(id="user-1")
    connections = [
        {
            "url": "http://one.example",
            "name": "One",
            "enabled": True,
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        },
        {
            "url": "http://two.example",
            "config": {"enable": False},
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True},
        },
    ]
    server_data = [
        {
            "idx": 0,
            "server_info": {"name": "Server One"},
            "capabilities": {"resources": {}, "prompts": {}},
            "tools": [{"name": "lookup"}, {"name": "preview"}],
            "prompts": [{"name": "Assist"}],
            "resources": [
                {
                    "tool_name": "lookup",
                    "id": "resource-1",
                    "render_url": "https://apps.example/render/1",
                    "mime_type": "text/html",
                    "metadata": {"tool_call_id": "call_1"},
                }
            ],
        }
    ]

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=connections,
    ), patch("open_webui.routers.configs.get_mcp_servers_data", return_value=server_data):
        result = asyncio.run(get_mcp_apps_capabilities(request, user))

    assert result["ENABLE_MCP_APPS"] is True
    assert result["servers"][0]["idx"] == 0
    assert result["servers"][0]["apps_enabled"] is True
    assert result["servers"][0]["resources"] == [
        {
            "server_idx": 0,
            "tool_name": "lookup",
            "app_id": "resource-1",
            "render_url": "https://apps.example/render/1",
            "resource_type": "resource",
            "title": None,
            "mime_type": "text/html",
            "content": None,
            "content_url": None,
            "metadata": {"tool_call_id": "call_1"},
        }
    ]
    assert result["servers"][0]["metadata"] == {
        "tool_count": 2,
        "tool_names": ["lookup", "preview"],
    }
    assert result["servers"][1]["idx"] == 1
    assert result["servers"][1]["enabled"] is False
    assert result["servers"][1]["apps_enabled"] is False
    assert result["servers"][1]["resources"] == []


def test_get_mcp_apps_capabilities_preserves_disabled_server_index_without_leaking_active_apps_metadata():
    from open_webui.routers.configs import get_mcp_apps_capabilities

    request = SimpleNamespace(state=SimpleNamespace(token=SimpleNamespace(credentials="tok_abc")))
    user = SimpleNamespace(id="user-1")
    connections = [
        {"url": "http://one.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
        {"url": "http://two.example", "enabled": False, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
    ]
    server_data = [
        {
            "idx": 0,
            "server_info": {"name": "Server One"},
            "capabilities": {"resources": {}},
            "tools": [{"name": "lookup"}],
            "resources": [{"id": "resource-1", "render_url": "https://apps.example/render/1"}],
        }
    ]

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=connections,
    ), patch("open_webui.routers.configs.get_mcp_servers_data", return_value=server_data):
        result = asyncio.run(get_mcp_apps_capabilities(request, user))

    assert result["ENABLE_MCP_APPS"] is True
    assert [server["idx"] for server in result["servers"]] == [0, 1]
    assert result["servers"][0]["apps_enabled"] is True
    assert result["servers"][0]["capabilities"] == {"resources": {}}
    assert result["servers"][0]["resources"] == [
        {
            "server_idx": 0,
            "tool_name": None,
            "app_id": "resource-1",
            "render_url": "https://apps.example/render/1",
            "resource_type": "resource",
            "title": None,
            "mime_type": None,
            "content": None,
            "content_url": None,
            "metadata": {},
        }
    ]
    assert result["servers"][1]["enabled"] is False
    assert result["servers"][1]["apps_enabled"] is False
    assert result["servers"][1]["capabilities"] == {}
    assert result["servers"][1]["resources"] == []
    assert result["servers"][1]["metadata"] == {"tool_count": 0, "tool_names": []}


def test_get_mcp_apps_capabilities_blanks_prompt_and_tool_metadata_for_disabled_base_connection():
    from open_webui.routers.configs import get_mcp_apps_capabilities

    request = SimpleNamespace(state=SimpleNamespace(token=SimpleNamespace(credentials="tok_abc")))
    user = SimpleNamespace(id="user-1")
    connections = [
        {"url": "http://one.example", "enabled": True, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
        {"url": "http://two.example", "enabled": False, "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": True}},
    ]
    server_data = [
        {
            "idx": 0,
            "server_info": {"name": "Server One"},
            "capabilities": {"resources": {}, "prompts": {}},
            "tools": [{"name": "lookup"}],
            "prompts": [{"name": "assist"}],
            "resources": [{"id": "resource-1", "render_url": "https://apps.example/render/1"}],
        },
        {
            "idx": 1,
            "server_info": {"name": "Server Two"},
            "capabilities": {"resources": {}, "prompts": {}},
            "tools": [{"name": "should-not-leak"}],
            "prompts": [{"name": "hidden"}],
            "resources": [{"id": "resource-2", "render_url": "https://apps.example/render/2"}],
        },
    ]

    with patch(
        "open_webui.routers.configs.get_user_mcp_server_connections",
        return_value=connections,
    ), patch("open_webui.routers.configs.get_mcp_servers_data", return_value=server_data):
        result = asyncio.run(get_mcp_apps_capabilities(request, user))

    assert [server["idx"] for server in result["servers"]] == [0, 1]
    assert result["servers"][0]["prompts"] == [{"name": "assist"}]
    assert result["servers"][0]["metadata"] == {"tool_count": 1, "tool_names": ["lookup"]}
    assert result["servers"][1]["enabled"] is False
    assert result["servers"][1]["apps_enabled"] is False
    assert result["servers"][1]["capabilities"] == {}
    assert result["servers"][1]["prompts"] == []
    assert result["servers"][1]["resources"] == []
    assert result["servers"][1]["metadata"] == {"tool_count": 0, "tool_names": []}


def test_get_mcp_server_data_fetches_resources_and_prompts_when_advertised():
    from open_webui.utils.mcp import get_mcp_server_data

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            self.calls = []

        async def initialize(self):
            self.calls.append("initialize")
            return {
                "serverInfo": {"name": "TestMCP"},
                "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
            }

        async def notify_initialized(self):
            self.calls.append("notify_initialized")

        async def list_tools(self):
            self.calls.append("list_tools")
            return [{"name": "echo"}]

        async def list_prompts(self):
            self.calls.append("list_prompts")
            return [{"name": "assist"}]

        async def list_resources(self):
            self.calls.append("list_resources")
            return [{"id": "res-1", "render_url": "https://apps.example/render/1"}]

    fake_client = FakeClient()

    with patch("open_webui.utils.mcp.MCPStreamableHttpClient", return_value=fake_client):
        result = asyncio.run(get_mcp_server_data({"url": "http://mcp.local"}))

    assert fake_client.calls == [
        "initialize",
        "notify_initialized",
        "list_tools",
        "list_prompts",
        "list_resources",
    ]
    assert result == {
        "server_info": {"name": "TestMCP"},
        "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
        "tools": [{"name": "echo"}],
        "prompts": [{"name": "assist"}],
        "resources": [{"id": "res-1", "render_url": "https://apps.example/render/1"}],
    }

