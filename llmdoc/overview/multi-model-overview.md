# 多模型集成概览

## 1. 身份

- **定义**: HaloWebUI 的多模型集成系统是一个统一的 AI 模型接入层，通过适配器模式将四个主流 AI 提供商（OpenAI、Anthropic Claude、Google Gemini、Ollama）接入统一的聊天接口。
- **目的**: 消除不同 AI 提供商 API 的差异，为用户提供一致的对话体验，同时支持灵活的模型切换和多连接管理。

## 2. 高层描述

系统采用"适配器模式"设计，所有 AI 提供商通过统一的后端 API 端点暴露。前端始终使用 OpenAI Chat Completions 格式发送请求，后端负责将请求转换为各提供商的原生格式，并将响应统一转换回 OpenAI 格式返回。

### 支持的提供商

| 提供商 | 路由模块 | API 端点 | 特性 |
|--------|----------|----------|------|
| OpenAI | `routers/openai.py` | `/api/chat/completions` | 支持 Chat Completions 和 Responses API，兼容 OpenRouter、Azure 等第三方代理 |
| Anthropic | `routers/anthropic.py` | `/api/anthropic/chat/completions` | 原生 Claude API，支持工具调用和文件上传 |
| Gemini | `routers/gemini.py` | `/api/gemini/chat/completions` | 支持 Google Search Grounding 和图像生成 |
| Ollama | `routers/ollama.py` | `/ollama/api/chat` | 本地模型代理，支持原生和 OpenAI 兼容端点 |

### 核心设计原则

1. **统一接口**: 所有请求通过 `/api/chat/completions` 进入，系统根据模型 ID 前缀自动路由
2. **用户级隔离**: 每个用户可配置独立的 API 连接，支持多账号切换
3. **格式透明**: 前端无需感知底层提供商差异，后端完成所有格式转换
4. **并行获取**: 模型列表获取采用并发 + 超时策略，避免单点阻塞

### 与其他模块的关系

- **认证系统**: 模型请求需要用户认证，连接配置存储在 `user.settings.ui.connections`
- **RAG 系统**: 文档检索结果作为上下文注入到聊天请求中
- **MCP 工具**: 工具调用结果通过统一格式传递给各提供商
