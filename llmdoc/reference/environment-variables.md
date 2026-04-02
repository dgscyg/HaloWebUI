# 环境变量参考

## 1. Core Summary

本文档提供 HaloWebUI 关键环境变量的快速参考。环境变量优先级最高，可覆盖数据库持久化配置。完整配置项请参考源文件。

## 2. Source of Truth

- **Primary Code:** `backend/open_webui/env.py` - 基础环境变量定义，应用启动时最先加载。
- **Persistent Config:** `backend/open_webui/config.py` - 持久化配置定义，包含更多可运行时修改的配置项。
- **Example File:** `.env.example` - 环境变量示例文件。
- **Related Architecture:** `/llmdoc/architecture/configuration-architecture.md` - 配置系统架构详情。

## 3. Key Environment Variables

### 3.1 基础配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATA_DIR` | `backend/data` | 数据存储目录 |
| `DATABASE_URL` | `sqlite:///.../webui.db` | 数据库连接 URL，支持 PostgreSQL |
| `DATABASE_ENCRYPTION_KEY` | - | SQLite SQLCipher 加密密钥 |
| `DATABASE_POOL_SIZE` | `0` | 数据库连接池大小 |
| `RESET_CONFIG_ON_START` | `False` | 启动时重置配置 |

### 3.2 Redis 配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `REDIS_URL` | - | Redis 连接 URL |
| `REDIS_KEY_PREFIX` | `open_webui:` | Redis 键前缀 |
| `REDIS_CLUSTER_MODE` | `false` | 启用 Redis Cluster 模式 |
| `REDIS_SENTINEL_HOSTS` | - | Redis Sentinel 主机列表 |
| `REDIS_SENTINEL_PORT` | `26379` | Redis Sentinel 端口 |

### 3.3 认证配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `WEBUI_AUTH` | `True` | 启用认证 |
| `WEBUI_SECRET_KEY` | `t0p-s3cr3t` | JWT 签名密钥 (生产环境必须修改) |
| `JWT_EXPIRES_IN` | `-1` | JWT 过期时间 (秒) |
| `ENABLE_API_KEY` | `True` | 启用 API Key 认证 |
| `ENABLE_GUEST_ACCESS` | `False` | 启用游客访问入口 |
| `GUEST_ACCESS_MODE` | `button` | 游客入口模式，`button` 显示按钮，`auto` 自动进入游客会话 |
| `WEBUI_ADMIN_EMAIL` | - | 自动创建管理员邮箱 |
| `WEBUI_ADMIN_PASSWORD` | - | 自动创建管理员密码 |

### 3.4 OAuth 配置

| 变量名 | 说明 |
|--------|------|
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | 飞书 OAuth |
| `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET` | 通用 OIDC |
| `ENABLE_OAUTH_SIGNUP` | 允许 OAuth 注册 (`False`) |

### 3.5 日志与审计

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `GLOBAL_LOG_LEVEL` | `INFO` | 全局日志级别 |
| `LOG_FORMAT` | `text` | 日志格式 (`text` / `json`) |
| `AUDIT_LOG_LEVEL` | `NONE` | 审计级别 (`METADATA`/`REQUEST`/`REQUEST_RESPONSE`) |
| `AUDIT_LOGS_FILE_PATH` | `{DATA_DIR}/audit.log` | 审计日志路径 |

### 3.6 WebSocket 配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_WEBSOCKET_SUPPORT` | `True` | 启用 WebSocket |
| `WEBSOCKET_MANAGER` | - | WebSocket 管理器类型 |
| `WEBSOCKET_REDIS_URL` | 同 `REDIS_URL` | WebSocket Redis URL |

### 3.7 可观测性

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_OTEL` | `False` | 启用 OpenTelemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP 导出端点 |
| `OTEL_SERVICE_NAME` | `open-webui` | 服务名称 |

### 3.8 Lite 预设

| 变量名 | 可选值 | 说明 |
|--------|--------|------|
| `HALOWEBUI_LITE_PRESET` | `free-lite`, `openai-compatible-lite` | 预设配置模式 |

**`free-lite` 预设:** 使用 Jina 免费嵌入/重排序，Web STT
**`openai-compatible-lite` 预设:** 使用 OpenAI 兼容 API，Docling 文档解析

### 3.9 MCP / 工具服务器

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA` | 项目默认值 | HTTP MCP / Tool Server 请求超时 |
| `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` | 空 | Tool Server / MCP HTTP SSL 校验配置 |
| `MCP_TOOL_CALL_TIMEOUT` | 项目默认值 | MCP 工具调用超时 |
| `MCP_STDIO_ALLOWED_COMMANDS` | 空 | 追加允许的 `stdio` 启动命令白名单 |
| `MCP_STDIO_START_TIMEOUT` | 项目默认值 | `stdio` MCP 初始化超时 |
| `MCP_STDIO_IDLE_TIMEOUT` | 项目默认值 | `stdio` MCP 空闲回收时间 |

## 4. Configuration Priority

```
环境变量 > 数据库持久化配置 > Lite 预设默认值 > 硬编码默认值
```

**注意:** 环境变量值在 `PersistentConfig` 初始化时读取，之后数据库配置优先。
