# 配置系统概览

## 1. Identity

- **What it is:** HaloWebUI 的三层配置管理架构，支持环境变量、数据库持久化和 Redis 分布式同步。
- **Purpose:** 提供灵活的配置管理机制，支持单机部署和多实例高可用场景下的配置统一管理。

## 2. High-Level Description

HaloWebUI 配置系统采用分层架构设计，优先级从高到低依次为：

1. **环境变量层** (`env.py`): 定义运行时必需的基础配置，优先级最高，适合容器化部署和敏感信息管理。
2. **持久化配置层** (`config.py` + 数据库): 支持运行时动态修改，配置存储在 SQLite/PostgreSQL 的 `config` 表中，通过管理界面可调。
3. **分布式同步层** (Redis): 可选层，用于多实例部署时配置实时同步，确保集群配置一致性。

**配置优先级:** 环境变量 > 数据库持久化配置 > 默认值

**核心特性:**

- 启动时自动从 `config.json` 迁移到数据库
- Lite 预设模式简化初始部署（`free-lite`、`openai-compatible-lite`）
- 支持 Redis Sentinel 和 Cluster 模式实现高可用
- 配置变更实时生效，无需重启服务

**配置分类:**

| 类别           | 主要配置项                                                                  |
| -------------- | --------------------------------------------------------------------------- |
| 认证           | WEBUI_AUTH, JWT_EXPIRES_IN, OAuth (Google/Microsoft/GitHub/飞书/OIDC), LDAP |
| API 连接       | Ollama, OpenAI, Gemini, Anthropic                                           |
| RAG/向量数据库 | Chroma, Milvus, Qdrant, OpenSearch, Elasticsearch, Pgvector                 |
| 网页搜索       | SearXNG, Google PSE, Brave, Kagi, Bing, Exa, Tavily, Jina                   |
| 图片生成       | OpenAI DALL-E, AUTOMATIC1111, ComfyUI                                       |
| 音频处理       | Whisper, OpenAI TTS/STT, Azure Speech, Deepgram                             |
| 用户权限       | 工作区访问、聊天功能、特性开关                                              |
| 任务系统       | 标题生成、标签生成、查询生成、自动补全                                      |
