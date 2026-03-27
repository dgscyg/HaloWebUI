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
| URL | 是 | MCP 服务器的 HTTP 端点地址 |
| 名称 | 否 | 服务器显示名称，便于识别 |
| 描述 | 否 | 服务器功能描述 |
| 认证类型 | 是 | 认证方式 (none/bearer/session/oauth21) |
| 密钥 | 条件 | Bearer/OAuth 认证所需的令牌 |
| 启用 | 是 | 是否启用该服务器 |

### 2.2 认证配置

根据 MCP 服务器要求选择认证类型:

- **none**: 无需认证
- **bearer**: 填写 Bearer Token
- **session**: 使用当前登录用户的会话 Token
- **oauth21**: 填写 OAuth 2.1 令牌

## 3. 使用预设模板

对于常见 MCP 服务商，可使用预设模板快速配置:

1. 在添加服务器弹窗中选择预设模板
2. 系统自动填充 URL 和认证信息
3. 补充必要的 API Key 等认证信息
4. 保存配置

## 4. 验证连接

保存前建议验证连接:

1. 填写完配置后点击 **验证** 按钮
2. 系统调用 `POST /configs/mcp_servers/verify` 测试连接
3. 成功后显示服务器信息和可用工具数量
4. 失败时检查 URL、认证信息是否正确

## 5. 启用/禁用服务器

- 切换服务器列表中的 **启用** 开关
- 禁用的服务器不会在工具发现阶段被查询
- 配置立即生效，无需重启服务

## 6. 验证配置成功

配置完成后，在对话中使用 AI 模型:

1. 启用支持工具调用的模型
2. 在对话设置中启用 MCP 服务器
3. AI 模型将自动发现并可调用 MCP 工具
4. 工具名格式为 `mcp_{idx}__{tool_name}`

## 7. 配置存储位置

MCP 配置存储于用户设置中:

- 存储路径: `user.settings["tools"]["mcp_server_connections"]`
- API 端点: `GET/POST /api/v1/configs/mcp_servers`
- 验证端点: `POST /api/v1/configs/mcp_servers/verify`

## 8. 常见问题

**Q: 连接超时怎么办?**

检查网络连通性，确认 MCP 服务器 URL 可访问。可通过环境变量 `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA` 调整超时时间。

**Q: SSL 证书问题?**

通过环境变量 `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` 配置:
- 空值: 使用系统默认 CA
- `false`/`0`: 禁用证书验证 (仅开发环境)
- 文件路径: 使用自定义 CA 证书

**Q: 工具名冲突?**

系统自动添加 `mcp_{idx}__` 前缀避免冲突。如需调整工具顺序，在服务器列表中拖动排序。
