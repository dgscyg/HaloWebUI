# HaloWebUI 项目概览

## 1. 身份

- **项目定义**: HaloWebUI 是一个功能丰富、可自托管的 AI 聊天界面平台，专注于多平台消息网关集成和企业级功能扩展。
- **核心目标**: 为用户提供统一的 AI 对话入口，支持通过 Web 界面、Telegram、企业微信、飞书等多种渠道与多个 AI 模型交互。

## 2. 项目定位

HaloWebUI 基于 [Open WebUI](https://github.com/open-webui/open-webui) 深度定制开发，在保留原项目核心功能的基础上，新增了 **HaloClaw 消息网关** 等特色模块，解决了以下问题:

- **多渠道统一接入**: 用户无需切换应用，即可在常用聊天工具（Telegram/企业微信/飞书）中使用 AI 能力
- **多模型灵活切换**: 支持 Claude、Gemini、OpenAI、Ollama 等主流模型的统一接入和切换
- **知识增强对话**: 内置 RAG 检索增强生成能力，支持文档知识库和网页搜索
- **工具扩展生态**: 集成 MCP (Model Context Protocol) 工具调用框架

## 3. 核心特性

### 3.1 HaloClaw 消息网关

HaloClaw 是 HaloWebUI 的核心特色模块，实现外部消息平台到 AI 聊天管道的统一接入:

- **支持平台**: Telegram（长轮询）、企业微信（Webhook）、飞书（Webhook）
- **访问控制**: 支持黑名单/白名单策略，灵活控制用户访问权限
- **消息持久化**: 自动记录对话历史，支持上下文连续对话
- **多模态支持**: 支持文本和图片消息的处理与响应

参见: `backend/open_webui/haloclaw/` 目录

### 3.2 多模型集成

系统通过适配器模式统一四大 AI 提供商:

| 提供商 | 路由模块 | 特性 |
|--------|----------|------|
| OpenAI | `routers/openai.py` | 支持 Chat Completions 和 Responses API |
| Anthropic Claude | `routers/anthropic.py` | 原生 Claude API，自动格式转换 |
| Google Gemini | `routers/gemini.py` | 支持 Google Search Grounding |
| Ollama | `routers/ollama.py` | 本地模型代理 |

参见: `backend/open_webui/routers/` 目录

### 3.3 RAG 知识检索增强

完整的检索增强生成系统:

- **向量数据库**: 支持 ChromaDB、Qdrant、Milvus、pgvector、OpenSearch、Elasticsearch
- **检索方式**: 纯向量搜索、混合搜索（BM25 + 向量）、重排序
- **嵌入模型**: 本地模型、Ollama、OpenAI 兼容 API
- **文档解析**: 支持 Tika、Docling、Azure Document Intelligence 等引擎

参见: `backend/open_webui/retrieval/` 目录

### 3.4 MCP 工具调用

完整实现 MCP (Model Context Protocol) Streamable HTTP 传输:

- **协议版本**: 2025-11-25 (JSON-RPC 2.0)
- **认证方式**: None、Bearer、Session、OAuth 2.1
- **预设服务器**: Composio、Smithery、Zapier、本地 stdio 桥接

参见: `backend/open_webui/utils/mcp.py`

## 4. 技术栈

### 4.1 前端

| 技术 | 版本/说明 |
|------|----------|
| 框架 | SvelteKit (Svelte 4) |
| 语言 | TypeScript |
| 样式 | Tailwind CSS |
| 状态管理 | Svelte Stores |
| 实时通信 | Socket.IO Client |

目录: `src/`

### 4.2 后端

| 技术 | 版本/说明 |
|------|----------|
| 框架 | FastAPI |
| 语言 | Python 3.10+ |
| ORM | SQLAlchemy + Pydantic |
| 认证 | JWT (HS256) |
| 实时通信 | Socket.IO |

目录: `backend/open_webui/`

### 4.3 数据存储

| 类型 | 支持选项 |
|------|----------|
| 关系数据库 | SQLite（默认）、PostgreSQL |
| 向量数据库 | ChromaDB、Qdrant、Milvus、pgvector 等 |
| 文件存储 | 本地存储、S3、GCS、Azure Blob |
| 缓存 | Redis（可选） |

## 5. 与 Open WebUI 的关系

HaloWebUI 是 Open WebUI 的深度定制分支，主要差异包括:

| 特性 | Open WebUI | HaloWebUI |
|------|------------|-----------|
| 消息网关 | 无 | HaloClaw (Telegram/企业微信/飞书) |
| 模型集成 | 标准支持 | 深度优化路由机制 |
| 配置系统 | 标准配置 | 支持从原版自动迁移 |
| UI 定制 | 标准 UI | 针对国内场景优化 |

迁移兼容: 支持从 Open WebUI 0.7.x ~ 0.8.10 自动迁移数据

## 6. 项目结构概览

```
HaloWebUI/
├── backend/open_webui/     # 后端 Python 代码
│   ├── main.py             # FastAPI 应用入口
│   ├── config.py           # 配置管理
│   ├── routers/            # API 路由模块
│   ├── models/             # 数据模型
│   ├── utils/              # 工具函数
│   ├── retrieval/          # RAG 检索模块
│   └── haloclaw/           # HaloClaw 消息网关
├── src/                    # 前端 Svelte 代码
│   ├── lib/
│   │   ├── components/     # UI 组件
│   │   ├── apis/           # API 调用层
│   │   └── stores/         # 状态管理
│   └── routes/             # SvelteKit 路由
└── llmdoc/                 # 项目文档
```

## 7. 快速了解各模块

详细架构信息请参阅:

- 认证系统: `llmdoc/agent/scout-auth.md`
- 后端架构: `llmdoc/agent/scout-backend.md`
- 前端架构: `llmdoc/agent/scout-frontend.md`
- HaloClaw 网关: `llmdoc/agent/scout-haloclaw.md`
- 模型集成: `llmdoc/agent/scout-models.md`
- RAG 系统: `llmdoc/agent/scout-rag.md`
- MCP 集成: `llmdoc/agent/scout-mcp.md`
- 存储系统: `llmdoc/agent/scout-storage.md`
- 配置系统: `llmdoc/agent/scout-config.md`
