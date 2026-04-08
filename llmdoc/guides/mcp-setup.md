# 如何配置 MCP 服务器

本指南说明如何在 HaloWebUI 中添加和配置 MCP (Model Context Protocol) 服务器。

## 1. 访问配置页面

1. 以管理员身份登录 HaloWebUI
2. 进入 **管理员面板** → **设置** → **工具**
3. 切换到 **MCP 服务器** 标签页

## 2. 添加 MCP 服务器

点击 **添加服务器** 按钮，在弹窗中填写配置:

### 2.1 基本配置字段

| 字段 | 必填 | 说明 |
|------|------|------|
| 传输方式 | 是 | `http` 或 `stdio` |
| URL | `http` 时必填 | MCP 服务器的 HTTP 端点地址 |
| Command | `stdio` 时必填 | 本地 MCP 进程启动命令 |
| Args / Env | `stdio` 时可选 | 本地进程参数与环境变量 |
| 名称 | 否 | 服务器显示名称，便于识别 |
| 描述 | 否 | 服务器功能描述 |
| 认证类型 | `http` 时使用 | 认证方式 (`none`/`bearer`/`session`/`oauth21`) |
| 密钥 | 条件 | Bearer / OAuth 认证所需的令牌 |
| 启用 | 是 | 是否启用该服务器 |

`stdio` 连接仅允许管理员保存和验证。

### 2.2 认证配置

根据 MCP 服务器要求选择认证类型:

- **none**: 无需认证
- **bearer**: 填写 Bearer Token
- **session**: 使用当前登录用户的会话 Token
- **oauth21**: 填写 OAuth 2.1 令牌

## 3. 使用预设模板

对于常见 MCP 服务商，可使用预设模板快速配置:

1. 在添加服务器弹窗中选择预设模板
2. 系统自动填充 HTTP URL，或 `stdio` 的 Command / Args
3. 补充必要的 API Key 等认证信息
4. 保存配置

## 4. 验证连接

保存前建议验证连接:

1. 填写完配置后点击 **验证** 按钮
2. 系统调用 `POST /configs/mcp_servers/verify` 测试连接
3. 成功后显示服务器信息和可用工具数量
4. 成功后记录最近验证时间，便于后续排查失效连接
5. 失败时检查 URL、认证信息或本地运行时依赖是否正确

## 5. MCP Apps

MCP 服务器支持暴露资源与提示时，可在 **MCP Apps** 面板中进一步配置:

1. 打开全局 `ENABLE_MCP_APPS`
2. 按服务器单独启用或禁用 Apps
3. 选择展示方式: 聊天区内联渲染，或右侧面板预览
4. 系统会通过 `GET /api/v1/configs/mcp_servers/apps/capabilities` 读取资源、提示和工具统计
5. `ui://` 资源通过 `GET /api/v1/configs/mcp_servers/apps/resource` 代理为同源可访问内容

## 6. 启用/禁用服务器

- 切换服务器列表中的 **启用** 开关
- 禁用的服务器不会在工具发现阶段被查询
- 配置立即生效，无需重启服务

## 7. 验证配置成功

配置完成后，在对话中使用 AI 模型:

1. 启用支持工具调用的模型
2. 在对话设置中启用 MCP 服务器
3. AI 模型将自动发现并可调用 MCP 工具
4. 工具名格式为 `mcp_{idx}__{tool_name}`

## 8. 配置存储位置

MCP 配置存储于用户设置中:

- 存储路径: `user.settings["tools"]["mcp_server_connections"]`
- `MCP Apps` 全局开关: `user.settings["tools"]["mcp_apps_config"]`
- API 端点: `GET/POST /api/v1/configs/mcp_servers`
- 验证端点: `POST /api/v1/configs/mcp_servers/verify`

## 9. 常见问题

**Q: 连接超时怎么办?**

检查网络连通性，确认 MCP 服务器 URL 可访问。可通过环境变量 `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA` 调整超时时间。

**Q: SSL 证书问题?**

通过环境变量 `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` 配置:
- 空值: 使用系统默认 CA
- `false`/`0`: 禁用证书验证 (仅开发环境)
- 文件路径: 使用自定义 CA 证书

**Q: 工具名冲突?**

系统自动添加 `mcp_{idx}__` 前缀避免冲突。如需调整工具顺序，在服务器列表中拖动排序。

**Q: stdio 验证失败怎么办?**

确认本机已安装对应运行时，并且命令名位于允许列表内。常见依赖包括 `node`/`npx`、`python`/`uv`/`uvx`、`deno`。
