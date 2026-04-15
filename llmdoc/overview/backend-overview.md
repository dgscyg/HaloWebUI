# 后端概览

## 1. 身份

- **项目定义**: HaloWebUI 后端是一个基于 Python FastAPI 构建的高性能 AI 聊天服务后端。
- **核心目标**: 为前端和多平台消息网关提供统一的 REST API，实现多模型 AI 对话、用户认证、文件管理和 RAG 检索等功能。

## 2. 技术栈

| 层级     | 技术                | 说明                                                                                                                        |
| -------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 框架     | FastAPI             | 异步 ASGI 框架，支持 OpenAPI 文档                                                                                           |
| 语言     | Python 3.10+        | 类型注解支持                                                                                                                |
| ORM      | SQLAlchemy 2.0      | 异步数据库访问                                                                                                              |
| 验证     | Pydantic v2         | 数据验证和序列化                                                                                                            |
| 认证     | JWT (HS256)         | 用户会话令牌                                                                                                                |
| 实时通信 | Socket.IO           | WebSocket 双向通信                                                                                                          |
| 数据库   | SQLite / PostgreSQL | 默认 SQLite，支持 PostgreSQL                                                                                                |
| 缓存     | Redis (可选)        | 配置同步、速率限制                                                                                                          |
| 容器构建 | Docker 多阶段构建   | `Dockerfile` 支持 `NPM_REGISTRY`、`DEBIAN_MIRROR`、`DEBIAN_SECURITY_MIRROR`、`PIP_INDEX_URL`、`PIP_TRUSTED_HOST` 覆盖镜像源 |

## 3. 核心模块

### 3.1 入口与配置

- `backend/open_webui/main.py`: FastAPI 应用入口，注册所有路由和中间件
- `backend/open_webui/config.py`: 配置管理系统，支持环境变量和数据库持久化

### 3.2 路由模块 (`routers/`)

| 路由前缀            | 模块               | 功能                                                                      |
| ------------------- | ------------------ | ------------------------------------------------------------------------- |
| `/api/v1/auths`     | auths.py           | 用户认证、登录、注册、OAuth、LDAP                                         |
| `/api/v1/chats`     | chats.py           | 聊天会话 CRUD、搜索、标签                                                 |
| `/api/v1/models`    | models.py          | 模型配置管理                                                              |
| `/api/v1/files`     | files.py           | 文件上传、元数据管理                                                      |
| `/api/v1/knowledge` | knowledge.py       | 知识库管理                                                                |
| `/api/v1/retrieval` | retrieval.py       | RAG 文档检索                                                              |
| `/api/v1/utils`     | utils.py           | 代码格式化、Markdown 转 HTML、聊天 PDF 导出；代码格式化依赖运行时 `black` |
| `/ollama`           | ollama.py          | Ollama API 兼容层                                                         |
| `/openai`           | openai.py          | OpenAI API 兼容层                                                         |
| `/gemini`           | gemini.py          | Google Gemini API                                                         |
| `/anthropic`        | anthropic.py       | Anthropic Claude API                                                      |
| `/api/v1/images`    | images.py          | 图像生成                                                                  |
| `/api/v1/audio`     | audio.py           | 语音转文字/文字转语音                                                     |
| `/api/v1/haloclaw`  | haloclaw/router.py | 消息网关管理                                                              |

### 3.3 数据模型 (`models/`)

核心数据表: `User`、`Auth`、`Chat`、`ChatMessage`、`Model`、`File`、`Group`、`Knowledge`、`Prompt`、`Tool`、`Function`

每个模型文件包含 SQLAlchemy 表定义、Pydantic DTO 和 Table 类封装的 CRUD 方法。

### 3.4 工具函数 (`utils/`)

- `auth.py`: JWT 令牌创建/验证、密码哈希、用户缓存
- `access_control.py`: 权限检查、资源访问控制
- `chat.py`: 聊天完成核心逻辑、多提供商路由
- `middleware.py`: 请求/响应中间件管道
- `models.py`: 模型获取和访问控制
- `mcp.py`: MCP 工具协议支持

## 4. 与其他模块的关系

- **前端**: 通过 REST API 和 WebSocket 与 SvelteKit 前端通信
- **HaloClaw**: 通过 `haloclaw/` 模块接入 Telegram/企业微信/飞书消息
- **RAG**: 通过 `retrieval/` 模块实现文档检索增强生成
- **外部 AI**: 通过各提供商路由模块连接 OpenAI、Claude、Gemini、Ollama

## 5. 详细架构

参见: `/llmdoc/architecture/backend-architecture.md`
