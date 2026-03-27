# HaloClaw 消息网关概览

## 1. 身份

- **项目定义**: HaloClaw 是 HaloWebUI 的消息网关模块，将外部消息平台连接到 AI 聊天管道。
- **核心目标**: 让用户通过日常使用的聊天应用（Telegram、企业微信、飞书）与 AI 模型交互，无需打开 Web 界面。

## 2. 支持平台

| 平台 | 接收模式 | 发送模式 | 特性 |
|------|----------|----------|------|
| Telegram | 长轮询 | Bot API | 私聊/群聊、命令菜单、内联键盘 |
| 企业微信 | Webhook 回调 | 企业 API | AES 加密消息、access_token 认证 |
| 飞书 | Webhook 事件订阅 | 开放平台 API | AES 加密、事件去重、群聊 @提及 |

## 3. 核心能力

### 3.1 消息处理

- **多模态支持**: 文本消息 + 图片消息（自动转换为 base64 data URL）
- **上下文对话**: 自动加载历史消息，支持连续对话
- **系统提示词**: 每个网关可配置独立的 system_prompt

### 3.2 访问控制

- **黑名单**: 阻止特定用户使用网关
- **白名单**: 仅允许白名单中的用户访问
- **群聊策略**: 可配置群聊响应模式（mention/disabled）

### 3.3 模型配置

- **三级模型优先级**: 用户覆盖 > 网关默认 > 全局默认
- **动态切换**: 用户可通过命令（如 `/model`）切换模型
- **思考强度**: 支持 reasoning_effort 参数配置

### 3.4 工具调用

- **内置工具**: 网关可配置允许的工具 ID 列表
- **多轮工具循环**: 自动执行工具调用直到返回最终响应

## 4. 关键配置

- `ENABLE_HALOCLAW`: 全局启用开关（环境变量或持久化配置）
- `HALOCLAW_DEFAULT_MODEL`: 全局默认模型 ID
- `HALOCLAW_MAX_HISTORY`: 最大历史消息条数（默认 20）
- `HALOCLAW_RATE_LIMIT`: 速率限制（默认 10）

## 5. 相关文档

- 架构设计: `/llmdoc/architecture/haloclaw-architecture.md`
- 配置指南: `/llmdoc/guides/haloclaw-setup.md`
- 详细报告: `/llmdoc/agent/scout-haloclaw.md`
