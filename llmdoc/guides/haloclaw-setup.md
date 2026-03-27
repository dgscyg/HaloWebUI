# 如何配置 HaloClaw 网关

本指南介绍如何配置一个 HaloClaw 消息网关，以 Telegram 为例。

## 前置条件

1. HaloWebUI 管理员账户
2. 目标平台的开发者凭证（如 Telegram Bot Token）

## 配置步骤

### 1. 启用 HaloClaw 模块

在管理界面或通过 API 启用：

```bash
# 通过环境变量
ENABLE_HALOCLAW=true

# 或通过 API（需管理员权限）
POST /api/v1/haloclaw/config
{"enabled": true}
```

### 2. 设置全局默认模型

```bash
POST /api/v1/haloclaw/config
{"default_model": "gpt-4o"}
```

### 3. 创建网关

```bash
POST /api/v1/haloclaw/gateways
{
  "platform": "telegram",
  "name": "我的 Telegram 机器人",
  "config": {
    "bot_token": "YOUR_BOT_TOKEN"
  },
  "default_model_id": "gpt-4o",
  "system_prompt": "你是一个有帮助的助手。",
  "enabled": false
}
```

**平台配置说明**:

| 平台 | 必需配置字段 |
|------|-------------|
| Telegram | `bot_token` |
| 企业微信 | `corp_id`, `agent_id`, `secret`, `token`, `aes_key` |
| 飞书 | `app_id`, `app_secret`, `verification_token`, `encrypt_key`(可选) |

### 4. 配置 Webhook（仅企业微信/飞书）

获取网关 ID 后，配置平台回调 URL：

- 企业微信: `https://your-domain/api/v1/haloclaw/webhook/wechat_work/{gateway_id}`
- 飞书: `https://your-domain/api/v1/haloclaw/webhook/feishu/{gateway_id}`

在企业微信/飞书管理后台填入对应 URL 并完成验证。

### 5. 启用网关

```bash
POST /api/v1/haloclaw/gateways/{gateway_id}/toggle
{"enabled": true}
```

启用后适配器会立即启动。

### 6. 验证配置

发送测试消息到配置的平台，检查是否收到 AI 响应。查看日志：

```bash
# 检查适配器启动状态
GET /api/v1/haloclaw/gateways

# 查看消息日志
GET /api/v1/haloclaw/gateways/{gateway_id}/logs
```

## 访问控制配置

### 白名单模式

```json
{
  "access_policy": {
    "dm_policy": "allowlist",
    "allowlist": ["user_id_1", "user_id_2"]
  }
}
```

### 群聊策略

```json
{
  "access_policy": {
    "group_policy": "mention"
  }
}
```

| 群聊策略 | 行为 |
|----------|------|
| `mention` | 仅在被 @提及时响应（默认） |
| `all` | 响应所有消息 |
| `disabled` | 群聊中不响应 |

## 工具调用配置

在网关的 `meta` 字段中配置允许的工具：

```json
{
  "meta": {
    "tool_ids": ["web_search", "calculator"],
    "max_tool_rounds": 5
  }
}
```

## 故障排查

1. **适配器未启动**: 检查 `config` 字段是否包含所有必需的凭证
2. **消息无响应**: 检查 `default_model_id` 是否有效，查看后端日志
3. **Webhook 验证失败**: 确认 token/aes_key 配置正确，检查签名验证逻辑
