# MCP 集成架构

## 1. 身份

- **项目定义**: MCP 集成模块负责实现 Model Context Protocol 的客户端功能，使 HaloWebUI 能够与 MCP 服务器通信。
- **核心目标**: 提供标准化的工具发现和调用机制，将 MCP 工具无缝集成到 AI 对话流程中。

## 2. 核心组件

- `backend/open_webui/utils/mcp.py` (MCPStreamableHttpClient, get_mcp_server_data, execute_mcp_tool): MCP 核心客户端实现，处理 JSON-RPC 通信、会话管理、工具调用。
- `backend/open_webui/utils/tools.py` (get_tools, make_mcp_function_name): 工具聚合入口，将 MCP 工具转换为 OpenAI 兼容函数规格。
- `backend/open_webui/utils/user_tools.py` (get_user_mcp_server_connections, set_user_mcp_server_connections): 用户级 MCP 配置存取。
- `backend/open_webui/routers/configs.py` (MCPServerConnection, get_mcp_servers_config, verify_mcp_server_connection): MCP 配置 API 端点。
- `backend/open_webui/routers/tools.py` (get_tools): 工具列表 API，聚合 MCP 工具。
- `src/lib/apis/configs/index.ts` (getMCPServerConnections, setMCPServerConnections, verifyMCPServerConnection): 前端 MCP API 函数。
- `src/lib/components/admin/Settings/Tools/MCPServerModal.svelte`: MCP 服务器配置 UI 组件。

## 3. 执行流程

```mermaid
sequenceDiagram
    participant UI as 前端 UI
    participant API as configs.py API
    participant MCP as mcp.py 客户端
    participant Server as MCP 服务器

    Note over UI,Server: 1. 配置阶段
    UI->>API: POST /configs/mcp_servers
    API->>API: 保存到 user.settings["tools"]["mcp_server_connections"]

    Note over UI,Server: 2. 验证阶段
    UI->>API: POST /configs/mcp_servers/verify
    API->>MCP: get_mcp_server_data()
    MCP->>Server: initialize (JSON-RPC)
    Server-->>MCP: serverInfo, capabilities
    MCP->>Server: notifications/initialized
    MCP->>Server: tools/list
    Server-->>MCP: 工具列表
    MCP-->>API: {server_info, tools}
    API-->>UI: 验证结果

    Note over UI,Server: 3. 工具发现阶段 (AI 对话时)
    UI->>API: GET /tools/
    API->>MCP: get_mcp_servers_data()
    MCP->>Server: 并发请求所有启用的服务器
    Server-->>MCP: 各服务器工具列表
    MCP-->>API: 聚合的工具数据
    API-->>UI: OpenAI 兼容函数规格

    Note over UI,Server: 4. 工具调用阶段
    UI->>API: AI 调用 mcp_0__tool_name
    API->>MCP: execute_mcp_tool()
    MCP->>Server: tools/call (JSON-RPC)
    Server-->>MCP: 执行结果 / SSE 进度通知
    MCP-->>API: 工具返回值
    API-->>UI: 响应结果
```

## 4. 数据流详解

### 4.1 配置存储

用户级配置存储于 `user.settings["tools"]["mcp_server_connections"]`:

```json
{
  "tools": {
    "mcp_server_connections": [
      {
        "url": "https://mcp.example.com/mcp",
        "name": "示例服务器",
        "auth_type": "bearer",
        "key": "xxx",
        "config": { "enable": true },
        "server_info": { ... },
        "tool_count": 5
      }
    ]
  }
}
```

### 4.2 工具发现流程

1. `routers/tools.py:get_tools` 端点被调用
2. 请求 `request.state.MCP_SERVERS` 获取预加载的服务器数据
3. 遍历每个 MCP 服务器的工具列表
4. 使用 `make_mcp_function_name()` 生成 OpenAI 兼容函数名
5. 将 MCP 工具的 `inputSchema` 转换为 OpenAI `parameters` 格式
6. 返回聚合后的工具字典

### 4.3 工具调用流程

`backend/open_webui/utils/tools.py:229-283`:

1. 解析工具名，提取 `server_idx` 和原始工具名
2. 获取对应的 MCP 服务器连接配置
3. 构建 `execute_mcp_tool()` 调用
4. 通过 `MCPStreamableHttpClient` 发送 JSON-RPC 请求
5. 可选：通过 `on_notification` 回调转发进度通知到 UI

## 5. JSON-RPC 方法映射

| MCP 操作 | JSON-RPC 方法 | 说明 |
|----------|---------------|------|
| 初始化 | `initialize` | 协商协议版本和能力 |
| 初始化通知 | `notifications/initialized` | 通知服务器客户端已就绪 |
| 工具列表 | `tools/list` | 获取可用工具及参数规格 |
| 工具调用 | `tools/call` | 执行指定工具 |

## 6. SSE 进度通知

MCP 服务器可通过 SSE 流发送进度通知:

| 通知类型 | 说明 |
|----------|------|
| `notifications/progress` | 执行进度 (progress/total) |
| `notifications/message` | 日志消息 (level/data) |

前端通过 `__event_emitter__` 回调接收并展示进度状态。

## 7. 设计要点

- **无状态会话**: 每次工具调用创建新的 MCP 客户端实例，避免会话状态管理复杂性
- **并发发现**: 使用 `asyncio.gather()` 并发获取多个 MCP 服务器的工具列表
- **错误隔离**: 单个 MCP 服务器连接失败不影响其他服务器的工具发现
- **名称清洗**: 工具名转换为 OpenAI 兼容格式，确保函数名合法且唯一
