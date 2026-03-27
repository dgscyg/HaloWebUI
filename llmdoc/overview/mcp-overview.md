# MCP (Model Context Protocol) 集成概览

## 1. 身份

- **项目定义**: MCP 是 Anthropic 定义的标准化协议，用于 AI 模型与外部工具/数据源之间的通信。
- **核心目标**: 提供统一的工具调用接口，使 AI 模型能够安全、标准化地访问外部能力和数据。

## 2. 功能描述

HaloWebUI 实现了完整的 MCP Streamable HTTP 传输方式集成，支持通过 MCP 协议连接外部工具服务器。系统集成后，AI 模型可自动发现并调用 MCP 服务器提供的工具。

### 2.1 协议规范

| 属性 | 值 |
|------|-----|
| 协议版本 | `2025-11-25` |
| 传输方式 | Streamable HTTP |
| 通信协议 | JSON-RPC 2.0 |
| 响应格式 | JSON / SSE (Server-Sent Events) |

### 2.2 支持的认证方式

| 认证类型 | 说明 |
|----------|------|
| `none` | 无认证 |
| `bearer` | Bearer Token 认证 |
| `session` | 使用当前用户会话 Token |
| `oauth21` / `oauth2` | OAuth 2.1 令牌认证 |

### 2.3 核心能力

- **工具发现**: 自动获取 MCP 服务器提供的工具列表及参数规格
- **工具调用**: 支持同步和流式两种调用模式
- **进度通知**: 支持 SSE 流式进度更新 (`notifications/progress`)
- **会话管理**: 支持 MCP Session ID 的自动管理
- **用户隔离**: 每个用户可独立配置自己的 MCP 服务器连接

## 3. 预设服务器模板

前端 UI 提供以下预设 MCP 服务器模板，简化配置流程:

| 模板 | 用途 |
|------|------|
| Composio | Composio 集成平台 |
| Smithery | Smithery 工具市场 |
| Zapier | Zapier 自动化集成 |
| 本地 stdio 桥接 | 本地 MCP 服务器代理 |

## 4. 工具命名规范

MCP 工具在转换为 OpenAI 兼容格式时，遵循以下命名规则:

```
mcp_{server_idx}__{sanitized_tool_name}
```

- `server_idx`: MCP 服务器在配置列表中的索引
- `sanitized_tool_name`: 原始工具名经清洗后的标识符（仅保留字母、数字、下划线）
- 总长度限制: 64 字符（适配 OpenAI 函数名限制）

示例: `mcp_0__web_search`
