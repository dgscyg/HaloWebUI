import asyncio
import json
import logging
import ssl
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
from uuid import uuid4

import aiohttp

from open_webui.env import (
    AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA,
    AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL,
)

log = logging.getLogger(__name__)


# MCP Streamable HTTP uses JSON-RPC 2.0 over HTTP. We only implement the minimum
# subset required for tool discovery and tool execution.
DEFAULT_MCP_PROTOCOL_VERSION = "2025-11-25"


def _get_ssl_context() -> Optional[ssl.SSLContext]:
    """Build an SSL context from AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL.

    - Empty string (default): use system default (certifi / OS CA bundle).
    - Path to a CA file/dir: custom certificate.
    - "false" / "0": disable verification (insecure, for dev only).
    """
    val = (AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL or "").strip()
    if not val:
        return None  # aiohttp default (system CA)
    if val.lower() in {"false", "0", "no"}:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    ctx = ssl.create_default_context(cafile=val)
    return ctx


def _strip_trailing_slash(url: str) -> str:
    return url[:-1] if url.endswith("/") else url


def _is_enabled(connection: Dict[str, Any]) -> bool:
    # Support both "config.enable" (Open WebUI-style) and legacy "enabled".
    cfg = connection.get("config") or {}
    if isinstance(cfg, dict) and "enable" in cfg:
        return bool(cfg.get("enable"))
    if "enabled" in connection:
        return bool(connection.get("enabled"))
    return True


def _get_auth_headers(connection: Dict[str, Any], session_token: Optional[str]) -> Dict[str, str]:
    auth_type = (connection.get("auth_type") or "none").lower()
    if auth_type in {"bearer", "oauth21", "oauth2", "oauth"}:
        key = connection.get("key") or ""
        if not key:
            return {}
        return {"Authorization": f"Bearer {key}"}
    if auth_type == "session":
        if not session_token:
            return {}
        return {"Authorization": f"Bearer {session_token}"}
    return {}


async def _read_jsonrpc_response(
    response: aiohttp.ClientResponse,
    request_id: str,
    on_notification: Optional[Callable[[Dict[str, Any]], Coroutine]] = None,
) -> Dict[str, Any]:
    """
    Parse either JSON or SSE (text/event-stream) JSON-RPC responses and return the message
    matching request_id.  When *on_notification* is provided, any JSON-RPC notification
    (a message without an ``id`` field, e.g. ``notifications/progress``) received on the
    SSE stream will be forwarded to the callback.
    """
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/event-stream" not in content_type:
        return await response.json()

    # SSE: read `data: {...}` lines and stop when we see the final JSON-RPC message for request_id.
    buffer = ""
    async for raw_line in response.content:
        try:
            line = raw_line.decode("utf-8", errors="ignore").strip()
        except Exception:
            continue

        if not line:
            continue

        if line.startswith("data:"):
            payload = line[len("data:") :].strip()
            if not payload:
                continue
            if payload == "[DONE]":
                break

            # Handle both one-line JSON and chunked JSON.
            candidate = payload if not buffer else buffer + payload
            try:
                msg = json.loads(candidate)
                buffer = ""
            except Exception:
                buffer = candidate
                continue

            if str(msg.get("id", "")) == str(request_id):
                return msg

            # Forward intermediate notifications (no id → JSON-RPC notification).
            if "id" not in msg and on_notification is not None:
                try:
                    await on_notification(msg)
                except Exception:
                    pass

    raise RuntimeError("MCP server closed the stream before sending a response.")


@dataclass
class MCPServerData:
    idx: int
    url: str
    server_info: Dict[str, Any]
    capabilities: Dict[str, Any]
    tools: List[Dict[str, Any]]
    prompts: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]


class MCPStreamableHttpClient:
    def __init__(
        self,
        url: str,
        *,
        auth_headers: Optional[Dict[str, str]] = None,
        protocol_version: str = DEFAULT_MCP_PROTOCOL_VERSION,
        timeout_s: Optional[int] = None,
    ):
        self.url = _strip_trailing_slash(url)
        self.auth_headers = auth_headers or {}
        self.protocol_version = protocol_version
        self.timeout_s = (
            timeout_s
            if timeout_s is not None
            else AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA
        )
        self.session_id: Optional[str] = None

    async def _post_jsonrpc(
        self,
        payload: Dict[str, Any],
        on_notification: Optional[Callable[[Dict[str, Any]], Coroutine]] = None,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.protocol_version,
            **self.auth_headers,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        timeout = aiohttp.ClientTimeout(total=self.timeout_s) if self.timeout_s else None

        ssl_ctx = _get_ssl_context()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.url, headers=headers, json=payload, ssl=ssl_ctx) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise RuntimeError(f"MCP HTTP {resp.status}: {body}")

                # Capture / update session id if present.
                session_id = resp.headers.get("Mcp-Session-Id") or resp.headers.get("MCP-Session-Id")

                msg = await _read_jsonrpc_response(
                    resp, str(payload.get("id", "")), on_notification=on_notification
                )
                return msg, session_id

    async def initialize(self) -> Dict[str, Any]:
        request_id = str(uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": self.protocol_version,
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "HaloWebUI", "version": "unknown"},
            },
        }
        msg, session_id = await self._post_jsonrpc(payload)
        if session_id:
            self.session_id = session_id
        if "error" in msg:
            raise RuntimeError(msg["error"])
        return msg.get("result", {}) or {}

    async def notify_initialized(self) -> None:
        # JSON-RPC notification: no id expected in response.
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.protocol_version,
            **self.auth_headers,
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        timeout = aiohttp.ClientTimeout(total=self.timeout_s) if self.timeout_s else None
        ssl_ctx = _get_ssl_context()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.url, headers=headers, json=payload, ssl=ssl_ctx) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise RuntimeError(f"MCP HTTP {resp.status}: {body}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        tools: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            request_id = str(uuid4())
            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/list",
                "params": {"cursor": cursor} if cursor else {},
            }
            msg, _ = await self._post_jsonrpc(payload)
            if "error" in msg:
                raise RuntimeError(msg["error"])

            result = msg.get("result", {}) or {}
            tools.extend(result.get("tools", []) or [])
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return tools

    async def _list_paginated(self, method: str, key: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            request_id = str(uuid4())
            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": {"cursor": cursor} if cursor else {},
            }
            msg, _ = await self._post_jsonrpc(payload)
            if "error" in msg:
                raise RuntimeError(msg["error"])

            result = msg.get("result", {}) or {}
            items.extend(result.get(key, []) or [])
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return items

    async def list_prompts(self) -> List[Dict[str, Any]]:
        return await self._list_paginated("prompts/list", "prompts")

    async def list_resources(self) -> List[Dict[str, Any]]:
        return await self._list_paginated("resources/list", "resources")

    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        on_notification: Optional[Callable[[Dict[str, Any]], Coroutine]] = None,
    ) -> Dict[str, Any]:
        request_id = str(uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        msg, _ = await self._post_jsonrpc(payload, on_notification=on_notification)
        if "error" in msg:
            raise RuntimeError(msg["error"])
        return msg.get("result", {}) or {}


async def get_mcp_server_data(
    connection: Dict[str, Any],
    *,
    session_token: Optional[str] = None,
    protocol_version: str = DEFAULT_MCP_PROTOCOL_VERSION,
) -> Dict[str, Any]:
    """
    Fetch tool metadata from an MCP server.
    Returns a dict containing server_info and tools.
    """
    url = connection.get("url") or ""
    if not url:
        raise ValueError("Missing MCP server URL")

    client = MCPStreamableHttpClient(
        url,
        auth_headers=_get_auth_headers(connection, session_token),
        protocol_version=protocol_version,
    )
    init_result = await client.initialize()
    await client.notify_initialized()
    tools = await client.list_tools()
    prompts = []
    resources = []
    capabilities = init_result.get("capabilities", {}) or {}

    if isinstance(capabilities, dict):
        try:
            if "prompts" in capabilities:
                prompts = await client.list_prompts()
        except Exception:
            prompts = []
        try:
            if "resources" in capabilities:
                resources = await client.list_resources()
        except Exception:
            resources = []

    return {
        "server_info": init_result.get("serverInfo", {}) or {},
        "capabilities": capabilities,
        "tools": tools,
        "prompts": prompts,
        "resources": resources,
    }


async def get_mcp_servers_data(
    servers: List[Dict[str, Any]],
    *,
    session_token: Optional[str] = None,
    protocol_version: str = DEFAULT_MCP_PROTOCOL_VERSION,
) -> List[Dict[str, Any]]:
    server_entries: List[Tuple[int, Dict[str, Any]]] = [
        (idx, server)
        for idx, server in enumerate(servers)
        if _is_enabled(server)
    ]

    tasks = [
        get_mcp_server_data(server, session_token=session_token, protocol_version=protocol_version)
        for (_, server) in server_entries
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[Dict[str, Any]] = []
    for (idx, server), response in zip(server_entries, responses):
        if isinstance(response, Exception):
            log.warning(f"Failed to connect to MCP server {server.get('url')}: {response}")
            continue

        results.append(
            {
                "idx": idx,
                "url": _strip_trailing_slash(server.get("url") or ""),
                "server_info": response.get("server_info", {}) or {},
                "capabilities": response.get("capabilities", {}) or {},
                "tools": response.get("tools", []) or [],
                "prompts": response.get("prompts", []) or [],
                "resources": response.get("resources", []) or [],
            }
        )

    return results


async def execute_mcp_tool(
    connection: Dict[str, Any],
    *,
    name: str,
    arguments: Dict[str, Any],
    session_token: Optional[str] = None,
    protocol_version: str = DEFAULT_MCP_PROTOCOL_VERSION,
    on_notification: Optional[Callable[[Dict[str, Any]], Coroutine]] = None,
) -> Dict[str, Any]:
    """
    Execute a tool via MCP (Streamable HTTP). Uses a fresh session per execution to keep the
    implementation simple and robust.

    When *on_notification* is provided, intermediate JSON-RPC notifications emitted by the
    MCP server during tool execution (e.g. ``notifications/progress``) are forwarded to
    the callback so the caller can relay them to the UI.
    """
    url = connection.get("url") or ""
    if not url:
        raise ValueError("Missing MCP server URL")

    client = MCPStreamableHttpClient(
        url,
        auth_headers=_get_auth_headers(connection, session_token),
        protocol_version=protocol_version,
    )
    await client.initialize()
    await client.notify_initialized()
    return await client.call_tool(name=name, arguments=arguments or {}, on_notification=on_notification)

