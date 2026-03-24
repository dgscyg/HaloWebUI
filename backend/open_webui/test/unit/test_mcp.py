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
            "mcp_apps": {"ENABLE_MCP_APPS": True, "enabled": False},
        }
    ]


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
            set_mcp_apps_config(request, MCPAppsConfigForm(ENABLE_MCP_APPS=True), user)
        )

    assert result == {"ENABLE_MCP_APPS": True}
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

