# 多模型集成架构

## 1. 身份

- **定义**: 多模型集成架构是 HaloWebUI 的 AI 提供商适配层，通过路由器和统一模型管理实现多提供商的无缝接入。
- **目的**: 为前端提供一致的 API 接口，同时支持各提供商的独特功能和优化策略。

## 2. 核心组件

### 后端路由器

- `backend/open_webui/routers/openai.py` (`generate_chat_completion`, `get_all_models`): OpenAI 兼容 API 处理入口，支持 Chat Completions 和 Responses API 两种模式，处理流式和非流式响应。
- `backend/open_webui/routers/anthropic.py` (`generate_chat_completion`, `_get_anthropic_user_config`): Anthropic Claude API 路由，将 OpenAI 格式请求转换为 Anthropic Messages API 格式，支持工具调用和文件上传。
- `backend/open_webui/routers/gemini.py` (`generate_chat_completion`, `_get_gemini_user_config`): Google Gemini API 路由，使用 REST v1beta 格式，支持 Google Search Grounding 和图像生成。
- `backend/open_webui/routers/ollama.py` (`generate_chat_completion`, `get_all_models`): Ollama 本地模型代理，支持 `/api/chat` 和 `/v1/chat/completions` 两种端点。

### 模型管理

- `backend/open_webui/utils/models.py` (`get_all_base_models`, `_fetch_all_base_models`): 统一的模型获取函数，并行从四个提供商获取模型列表并合并，支持用户级缓存。
- `backend/open_webui/utils/user_connections.py` (`get_user_connections`, `maybe_migrate_user_connections`): 用户连接配置管理，实现用户级别的 API 配置隔离和迁移。

### 前端 API 层

- `src/lib/apis/openai/index.ts` (`chatCompletion`): 前端 OpenAI API 封装，通过统一的 `/api/chat/completions` 端点发送请求。
- `src/lib/apis/streaming/index.ts` (`createOpenAITextStream`): 前端流式响应解析器，解析 SSE 格式的响应流，支持大文本分块和图像流式传输。

## 3. 执行流程 (LLM 检索图)

### 请求路由流程

```
用户请求 → /api/chat/completions
         ↓
    模型 ID 前缀解析
         ↓
    ┌────┴────┬─────────┬─────────┐
    ↓         ↓         ↓         ↓
OpenAI   Anthropic   Gemini    Ollama
路由器     路由器     路由器     路由器
    ↓         ↓         ↓         ↓
 格式转换   格式转换   格式转换   直接代理
    ↓         ↓         ↓         ↓
 各提供商原生 API 调用
    ↓         ↓         ↓         ↓
 响应转换回 OpenAI 格式
    └────┬────┴─────────┴─────────┘
         ↓
    统一 SSE 流返回前端
```

### 详细步骤

1. **请求接收**: 前端通过 `src/lib/apis/openai/index.ts:chatCompletion()` 发送请求到 `/api/chat/completions`
2. **路由选择**: 后端根据模型 ID 中的 `prefix_id` 前缀（如 `abc12345.gpt-4o`）确定目标连接和提供商
3. **配置解析**: `_get_*_user_config()` 函数从 `user.settings.ui.connections.{provider}` 提取 URL、Key 和配置
4. **格式转换**: 各路由器将 OpenAI 格式转换为原生格式（Anthropic/Gemini）或直接透传（OpenAI/Ollama）
5. **流式响应**: 使用 `StreamingResponse` 包装响应流，各提供商格式转换为 OpenAI SSE 格式
6. **前端解析**: `createOpenAITextStream()` 解析 SSE 流并渲染

### 模型列表获取流程

1. **并发请求**: `_fetch_all_base_models()` 使用 `asyncio.gather()` 并行调用四个提供商的 `get_all_models()`
2. **超时控制**: 每个提供商使用独立超时（默认 5 秒），避免单个慢连接阻塞
3. **结果合并**: 合并所有提供商返回的模型，添加 `owned_by` 字段标识来源
4. **缓存机制**: 用户级缓存（TTL 5 分钟），后台自动刷新

## 4. 模型路由机制 (prefix_id)

每个连接配置拥有唯一的 `prefix_id`，用于模型路由：

- **格式**: `{prefix_id}.{model_name}`（如 `abc12345.gpt-4o`）
- **解析**: `_resolve_*_connection_by_model_id()` 函数在各路由器中提取前缀匹配连接
- **默认连接**: 无前缀时使用索引 0 的连接配置

### 连接配置存储

```
user.settings.ui.connections = {
  openai: {
    OPENAI_API_BASE_URLS: ["https://api.openai.com/v1"],
    OPENAI_API_KEYS: ["sk-xxx"],
    OPENAI_API_CONFIGS: {
      "0": { "prefix_id": "abc12345", ... }
    }
  },
  gemini: { ... },
  anthropic: { ... },
  ollama: { ... }
}
```

## 5. 流式响应处理

| 提供商    | 输入格式         | 输出格式 | 转换逻辑              |
| --------- | ---------------- | -------- | --------------------- |
| OpenAI    | SSE              | SSE      | 直接透传              |
| Anthropic | Anthropic Events | SSE      | `anthropic.py` 内转换 |
| Gemini    | NDJSON           | SSE      | `gemini.py` 内转换    |
| Ollama    | NDJSON           | NDJSON   | 直接透传              |

前端统一使用 `EventSourceParserStream` 解析 SSE 格式。
