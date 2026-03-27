"""
MCP (Model Context Protocol) Router.

基于 Open WebUI MCP Apps 参考实现，提供前端 AppBridge 所需的资源读取、
工具调用、资源列表和提示列表接口。当前仓库使用用户级 MCP 连接配置，
因此 server_id 适配为连接索引字符串。
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from open_webui.models.users import UserModel
from open_webui.routers.configs import (
    _get_mcp_apps_form_state,
    _is_mcp_connection_enabled,
    _pick_mcp_resource_content,
)
from open_webui.utils.auth import get_verified_user
from open_webui.utils.mcp import execute_mcp_tool, get_mcp_server_data, read_mcp_resource
from open_webui.utils.user_tools import get_user_mcp_server_connections

log = logging.getLogger(__name__)

router = APIRouter()


class McpUiResourceCsp(BaseModel):
    connectDomains: Optional[list[str]] = None
    resourceDomains: Optional[list[str]] = None
    frameDomains: Optional[list[str]] = None
    baseUriDomains: Optional[list[str]] = None


class MCPUIPermissions(BaseModel):
    camera: Optional[dict[str, Any]] = None
    microphone: Optional[dict[str, Any]] = None
    geolocation: Optional[dict[str, Any]] = None
    clipboardWrite: Optional[dict[str, Any]] = None


class MCPAppResource(BaseModel):
    uri: str
    content: str
    mimeType: str
    csp: Optional[McpUiResourceCsp] = None
    permissions: Optional[MCPUIPermissions] = None


class MCPToolResult(BaseModel):
    content: list[dict[str, Any]] = Field(default_factory=list)
    structuredContent: Any = Field(default_factory=dict)
    isError: bool = False


class ReadResourceRequest(BaseModel):
    server_id: str
    uri: str


class ReadResourceResponse(BaseModel):
    resource: MCPAppResource


class CallToolRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ListResourcesRequest(BaseModel):
    server_id: str


class ListPromptsRequest(BaseModel):
    server_id: str


def _resolve_server_index(connections: list[dict], server_id: str) -> int:
    normalized_server_id = str(server_id or "").strip()
    if not normalized_server_id:
        raise HTTPException(status_code=404, detail="MCP server not found")

    try:
        server_idx = int(normalized_server_id)
    except Exception:
        server_idx = -1

    if 0 <= server_idx < len(connections):
        return server_idx

    for idx, connection in enumerate(connections):
        server_info = connection.get("server_info") or {}
        candidate_ids = [
            connection.get("id"),
            connection.get("name"),
            server_info.get("id"),
            server_info.get("name"),
        ]
        if normalized_server_id in {
            str(candidate or "").strip() for candidate in candidate_ids if candidate
        }:
            return idx

    raise HTTPException(
        status_code=404,
        detail=f"MCP server '{normalized_server_id}' not found",
    )


def _normalize_tool_result_content(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        return result.get("content") or []
    if isinstance(result, list):
        return result
    if result is None:
        return [{"type": "text", "text": ""}]
    if isinstance(result, str):
        return [{"type": "text", "text": result}]
    return [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]


def _normalize_tool_result_structured_content(result: Any) -> Any:
    if isinstance(result, dict):
        return result.get("structuredContent") or {}
    return {}


def _extract_resource_ui_metadata(resource_catalog: dict[str, Any], uri: str) -> tuple[Optional[dict], Optional[dict]]:
    for resource in resource_catalog.get("resources", []) or []:
        if not isinstance(resource, dict):
            continue
        if str(resource.get("uri") or "").strip() != uri:
            continue

        meta = resource.get("meta") or resource.get("_meta") or {}
        if not isinstance(meta, dict):
            return None, None

        ui_meta = meta.get("ui") or {}
        if not isinstance(ui_meta, dict):
            return None, None

        csp = ui_meta.get("csp")
        permissions = ui_meta.get("permissions")
        return (
            csp if isinstance(csp, dict) else None,
            permissions if isinstance(permissions, dict) else None,
        )

    return None, None


def _get_mcp_connection(
    request: Request,
    user: UserModel,
    server_id: str,
    *,
    check_mcp_apps: bool = False,
) -> tuple[int, dict]:
    connections = get_user_mcp_server_connections(request, user)
    server_idx = _resolve_server_index(connections, server_id)
    connection = connections[server_idx]

    if check_mcp_apps:
        base_enabled = _is_mcp_connection_enabled(connection)
        apps_global_enabled, server_apps_enabled = _get_mcp_apps_form_state(
            connection,
            default_global_enabled=False,
        )
        if not (base_enabled and apps_global_enabled and server_apps_enabled):
            raise HTTPException(
                status_code=403,
                detail=f"MCP Apps are disabled for server '{server_id}'",
            )

    return server_idx, connection


@router.post("/resource", response_model=ReadResourceResponse)
async def read_resource(
    request: Request,
    body: ReadResourceRequest,
    user: UserModel = Depends(get_verified_user),
):
    _, connection = _get_mcp_connection(
        request,
        user,
        body.server_id,
        check_mcp_apps=True,
    )
    session_token = getattr(getattr(request.state, "token", None), "credentials", None)

    try:
        resource_catalog = await get_mcp_server_data(
            connection,
            session_token=session_token,
        )
        csp_data, permissions_data = _extract_resource_ui_metadata(resource_catalog, body.uri)

        resource_result = await read_mcp_resource(
            connection,
            uri=body.uri,
            session_token=session_token,
        )
        selected = _pick_mcp_resource_content(resource_result, body.uri)
        if not selected:
            raise HTTPException(status_code=404, detail="Resource not found")

        content = ""
        if isinstance(selected.get("text"), str):
            content = selected.get("text") or ""
        elif isinstance(selected.get("blob"), str):
            content = selected.get("blob") or ""

        mime_type = str(
            selected.get("mimeType")
            or selected.get("mime_type")
            or "text/html"
        ).strip() or "text/html"

        return ReadResourceResponse(
            resource=MCPAppResource(
                uri=body.uri,
                content=content,
                mimeType=mime_type,
                csp=McpUiResourceCsp(**csp_data) if csp_data else None,
                permissions=MCPUIPermissions(**permissions_data) if permissions_data else None,
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.error("Failed to read MCP resource '%s': %s", body.uri, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read resource: {str(exc)}",
        )


@router.post("/tool/call", response_model=MCPToolResult)
async def call_tool(
    request: Request,
    body: CallToolRequest,
    user: UserModel = Depends(get_verified_user),
):
    _, connection = _get_mcp_connection(
        request,
        user,
        body.server_id,
        check_mcp_apps=True,
    )
    session_token = getattr(getattr(request.state, "token", None), "credentials", None)

    try:
        result = await execute_mcp_tool(
            connection,
            name=body.tool_name,
            arguments=body.arguments or {},
            session_token=session_token,
        )
        return MCPToolResult(
            content=_normalize_tool_result_content(result),
            structuredContent=_normalize_tool_result_structured_content(result),
            isError=bool(result.get("isError")) if isinstance(result, dict) else False,
        )
    except Exception as exc:
        log.error("MCP tool call failed for '%s': %s", body.tool_name, exc)
        return MCPToolResult(
            content=[{"type": "text", "text": str(exc)}],
            structuredContent={},
            isError=True,
        )


@router.post("/resources")
async def list_resources(
    request: Request,
    body: ListResourcesRequest,
    user: UserModel = Depends(get_verified_user),
):
    _, connection = _get_mcp_connection(request, user, body.server_id)
    session_token = getattr(getattr(request.state, "token", None), "credentials", None)

    try:
        server_data = await get_mcp_server_data(
            connection,
            session_token=session_token,
        )
        return {"resources": server_data.get("resources", []) or []}
    except Exception as exc:
        log.error("Failed to list MCP resources for '%s': %s", body.server_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list resources: {str(exc)}",
        )


@router.post("/prompts")
async def list_prompts(
    request: Request,
    body: ListPromptsRequest,
    user: UserModel = Depends(get_verified_user),
):
    _, connection = _get_mcp_connection(request, user, body.server_id)
    session_token = getattr(getattr(request.state, "token", None), "credentials", None)

    try:
        server_data = await get_mcp_server_data(
            connection,
            session_token=session_token,
        )
        return {"prompts": server_data.get("prompts", []) or []}
    except Exception as exc:
        log.error("Failed to list MCP prompts for '%s': %s", body.server_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list prompts: {str(exc)}",
        )
