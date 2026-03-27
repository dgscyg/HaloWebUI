# 如何配置多模型 API 连接

本指南介绍如何为 HaloWebUI 配置各 AI 提供商的 API 连接。支持两种配置方式：管理员全局配置和用户个人配置。

## 1. 环境变量配置（管理员）

管理员可通过环境变量配置全局默认连接，作为所有用户的初始配置。

### OpenAI 兼容 API

```bash
# 启用 OpenAI API
ENABLE_OPENAI_API=true

# 单个连接
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxxxxxx

# 多个连接（分号分隔）
OPENAI_API_BASE_URLS=https://api.openai.com/v1;https://openrouter.ai/api/v1
OPENAI_API_KEYS=sk-xxxxxxxx;sk-or-xxxxxxxx
```

### Anthropic Claude

```bash
# 启用 Anthropic API
ENABLE_ANTHROPIC_API=true

# API 配置
ANTHROPIC_API_BASE_URLS=https://api.anthropic.com/v1
ANTHROPIC_API_KEYS=sk-ant-xxxxxxxx
```

### Google Gemini

```bash
# 启用 Gemini API
ENABLE_GEMINI_API=true

# API 配置
GEMINI_API_BASE_URLS=https://generativelanguage.googleapis.com/v1beta
GEMINI_API_KEYS=AIzaxxxxxxxx
```

### Ollama 本地模型

```bash
# Ollama 服务地址
OLLAMA_BASE_URLS=http://localhost:11434

# Docker 环境常用配置
# USE_OLLAMA_DOCKER=true 时自动使用 http://localhost:11434
```

## 2. 用户界面配置

普通用户可通过 Web 界面配置个人 API 连接：

1. **进入设置**: 点击右上角头像 → 设置 → 连接
2. **选择提供商**: 切换 OpenAI / Gemini / Anthropic / Ollama 标签页
3. **添加连接**: 点击"添加连接"按钮
4. **填写信息**:
   - API 基础 URL（如 `https://api.openai.com/v1`）
   - API 密钥
   - 连接名称（可选，用于识别）
5. **保存并验证**: 点击保存，系统自动验证连接并获取模型列表

## 3. 配置存储位置

- **管理员配置**: 存储在 `config` 数据库表中，键名为 `{provider}.api_keys`、`{provider}.api_base_urls` 等
- **用户配置**: 存储在 `user.settings.ui.connections` JSON 字段中

## 4. 验证连接状态

保存配置后，前端会调用验证接口检查连接有效性：

- OpenAI: `GET /api/config/connections/openai/verify`
- Gemini: `GET /api/config/connections/gemini/verify`
- Anthropic: `GET /api/config/connections/anthropic/verify`
- Ollama: `GET /api/config/connections/ollama/verify`

验证成功后自动获取可用模型列表。

## 5. 常见问题

### 模型列表为空

检查 API Key 权限和网络连通性。部分代理服务可能不支持 `/models` 端点，需手动添加模型 ID。

### 连接超时

调整 `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` 环境变量（默认 5 秒）增加超时时间。

### 多连接路由

当配置多个连接时，模型 ID 会带有前缀（如 `abc12345.gpt-4o`），系统根据前缀路由到对应连接。
