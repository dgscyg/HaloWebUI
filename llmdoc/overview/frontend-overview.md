# 前端概览

## 1. 身份

- **项目定义**: HaloWebUI 前端是一个基于 SvelteKit 的现代化 AI 聊天界面，提供多模型交互、实时流式响应和丰富的功能扩展。
- **核心目标**: 为用户提供响应式、可扩展的 Web 界面，支持多 AI 模型切换、知识库检索、工具调用等高级功能。

## 2. 高层级描述

前端采用 SvelteKit 框架构建，使用 TypeScript 提供类型安全，Tailwind CSS 处理样式。架构设计遵循组件化原则，组件按功能域组织（chat、layout、common、admin、channel）。状态管理使用 Svelte 原生的 writable store，所有状态集中在 `src/lib/stores/index.ts` 统一管理。API 层完全模块化，每个功能域独立文件，统一使用 fetch API 和 Bearer Token 认证。通过 Socket.IO 实现 WebSocket 实时通信，支持聊天事件推送和流式响应。

## 3. 技术栈

| 技术 | 版本/说明 |
|------|----------|
| 框架 | SvelteKit (Svelte 4) |
| 语言 | TypeScript |
| 样式 | Tailwind CSS |
| 状态管理 | Svelte Stores (writable) |
| 实时通信 | Socket.IO Client |
| 流式处理 | EventSourceParserStream (SSE) |

## 4. 核心目录结构

```
src/
├── lib/
│   ├── components/     # UI 组件（按功能域组织）
│   ├── apis/           # API 调用层（按功能域模块化）
│   ├── stores/         # 状态管理（集中式）
│   ├── services/       # 业务服务层
│   └── utils/          # 工具函数
└── routes/             # SvelteKit 文件系统路由
    ├── (app)/          # 需认证的应用页面
    ├── auth/           # 登录/注册
    └── s/[id]/         # 分享页面
```

## 5. 关键特性

- **多模型支持**: OpenAI、Ollama、Gemini、Anthropic 四大 AI 提供商的统一接入
- **流式响应**: SSE 解析实现大文本分块渲染
- **实时通信**: Socket.IO WebSocket 支持聊天事件推送
- **组件化架构**: 200+ Svelte 组件，按功能域清晰组织
- **响应式设计**: 支持桌面和移动端适配
