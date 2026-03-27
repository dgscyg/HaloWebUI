# HaloWebUI 文档索引

本目录为 HaloWebUI 项目的 LLM 优化文档系统，专为 AI 辅助开发设计。

## 概览 (Overview)

项目级别的宏观描述，回答"这是什么项目"。

- [项目概览](overview/project-overview.md) - HaloWebUI 的定义、核心特性、技术栈及与 Open WebUI 的关系
- [前端概览](overview/frontend-overview.md) - 前端技术栈（Svelte 4/TypeScript/Tailwind）、组件组织、核心特性
- [后端概览](overview/backend-overview.md) - FastAPI 后端技术栈、核心模块、与前后端关系
- [多模型集成概览](overview/multi-model-overview.md) - 支持的 AI 提供商（OpenAI/Claude/Gemini/Ollama）及统一接口设计
- [数据存储概览](overview/storage-overview.md) - 数据库和文件存储系统的整体介绍
- [HaloClaw 概览](overview/haloclaw-overview.md) - 消息网关模块：支持平台、核心能力、关键配置
- [MCP 集成概览](overview/mcp-overview.md) - Model Context Protocol 集成的协议版本、支持特性、认证方式
- [RAG 系统概览](overview/rag-overview.md) - RAG 检索增强生成系统的定义、核心能力与技术架构要点
- [认证系统概览](overview/authentication-overview.md) - 多策略身份验证框架：JWT、OAuth、LDAP、API Key
- [配置系统概览](overview/configuration-overview.md) - 三层配置管理架构：环境变量、数据库持久化、Redis 同步

## 架构 (Architecture)

系统构建方式，回答"系统如何运作"。

- [前端架构](architecture/frontend-architecture.md) - 组件目录结构、状态管理（stores）、API 层、路由结构、执行流程
- [后端架构](architecture/backend-architecture.md) - 目录结构、API 路由设计、中间件栈、请求生命周期
- [多模型集成架构](architecture/multi-model-architecture.md) - 提供商适配器、模型路由机制（prefix_id）、请求/响应流程、流式处理
- [存储架构](architecture/storage-architecture.md) - 数据库模型、ORM 使用、迁移系统、文件存储抽象
- [HaloClaw 架构](architecture/haloclaw-architecture.md) - 适配器模式设计、消息流程、数据模型、生命周期管理
- [MCP 集成架构](architecture/mcp-architecture.md) - MCP 客户端实现、工具命名规范、执行流程图
- [RAG 系统架构](architecture/rag-architecture.md) - 向量数据库连接器、嵌入引擎、检索流程、重排序机制
- [认证系统架构](architecture/authentication-architecture.md) - JWT Token 生命周期、OAuth 集成、权限计算流程
- [配置系统架构](architecture/configuration-architecture.md) - 环境变量解析、持久化存储、分布式同步机制

## 指南 (Guides)

分步操作指南，回答"如何做某事"。

- [前端开发指南](guides/frontend-development.md) - 如何添加新组件、API 模块、页面路由和全局状态
- [后端开发指南](guides/backend-development.md) - 如何添加新的 API 端点
- [多模型配置指南](guides/multi-model-configuration.md) - 配置各 AI 提供商（OpenAI/Claude/Gemini/Ollama）的 API 连接
- [存储配置指南](guides/storage-configuration.md) - 配置 PostgreSQL、S3、GCS、Azure 等存储后端
- [HaloClaw 网关配置](guides/haloclaw-setup.md) - 如何配置 Telegram/企业微信/飞书网关
- [MCP 服务器配置指南](guides/mcp-setup.md) - 如何添加、配置、验证 MCP 服务器连接
- [RAG 系统配置](guides/rag-setup.md) - 嵌入模型、向量数据库、重排序模型、知识库的配置指南
- [认证配置指南](guides/authentication-setup.md) - 配置本地认证、OAuth 提供商、LDAP、可信头部认证

## 参考 (Reference)

事实性查找信息，回答"X 的具体细节"。

- [编码规范](reference/coding-conventions.md) - 前端 TypeScript/Svelte 和后端 Python 的编码规范
- [Git 约定](reference/git-conventions.md) - 分支策略、提交信息格式
- [环境变量参考](reference/environment-variables.md) - 关键环境变量的快速参考表

## 快速开始

1. **了解项目**: 先阅读 [项目概览](overview/project-overview.md)
2. **深入模块**: 根据需要查阅对应架构文档
3. **代码定位**: 架构文档中包含精确的文件路径和函数引用

## 约定

- 所有路径均为相对于项目根目录的相对路径
- 代码引用格式: `path/to/file.ext:line_range` 或 `path/to/file.ext (SymbolName)`
