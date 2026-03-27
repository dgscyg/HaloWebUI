# 编码规范

本文档汇总项目核心编码规则，供快速查阅。

## 1. 核心摘要

项目采用 SvelteKit + TypeScript 前端与 FastAPI + Python 后端的分离架构。前端使用静态适配器构建，Tailwind CSS 处理样式并支持暗色模式。代码格式化由 Prettier 统一管理，ESLint 负责代码质量检查。

## 2. 真理来源

- **ESLint 配置:** `.eslintrc.cjs` - TypeScript/Svelte 代码质量规则
- **Prettier 配置:** `.prettierrc` - 代码格式化规则
- **TypeScript 配置:** `tsconfig.json` - TypeScript 编译选项
- **Svelte 配置:** `svelte.config.js` - SvelteKit 构建配置
- **Tailwind 配置:** `tailwind.config.js` - 样式系统配置
- **Python 依赖:** `pyproject.toml` - Python 项目配置与依赖

## 3. 前端规范 (TypeScript/Svelte)

### TypeScript

- 严格模式开启 (`strict: true`)
- 允许 JS 文件但启用检查 (`allowJs: true`, `checkJs: true`)
- 强制文件名大小写一致 (`forceConsistentCasingInFileNames: true`)
- 启用 JSON 模块解析 (`resolveJsonModule: true`)

### SvelteKit

- 使用 `adapter-static` 静态构建，输出至 `build/` 目录
- 使用 `vitePreprocess` 预处理器
- 忽略 `css-unused-selector` 警告

### ESLint 扩展

- `eslint:recommended` - ESLint 推荐规则
- `plugin:@typescript-eslint/recommended` - TypeScript 推荐规则
- `plugin:svelte/recommended` - Svelte 推荐规则
- `plugin:cypress/recommended` - Cypress 测试规则
- `prettier` - 禁用与 Prettier 冲突的规则

## 4. 样式规范 (Tailwind CSS)

### 核心配置

- **暗色模式:** `class` 策略（通过 `.dark` 类切换）
- **内容扫描:** `./src/**/*.{html,js,svelte,ts}`
- **插件:** `@tailwindcss/typography`, `@tailwindcss/container-queries`

### 自定义扩展

- **灰度色阶:** 自定义 `gray-50` 至 `gray-950`，支持 CSS 变量覆盖
- **字体族:** 以 `HarmonyOS Sans SC` 为首选的中文字体栈
- **安全区域内边距:** `p-safe-bottom` 适配移动端底部安全区

## 5. 后端规范 (Python/FastAPI)

### 版本要求

- Python `>= 3.11, < 3.13.0a1`

### 核心框架

- **Web 框架:** FastAPI 0.115.7
- **数据验证:** Pydantic 2.10.6
- **ASGI 服务器:** Uvicorn 0.34.0
- **数据库 ORM:** SQLAlchemy 2.0.38 + Peewee 3.17.9

### 代码格式化

- 使用 Black 25.1.0 进行 Python 代码格式化
- 使用 Codespell 进行拼写检查

## 6. 代码格式化规则 (Prettier)

| 规则 | 值 |
|------|-----|
| 缩进 | Tab |
| 引号 | 单引号 |
| 尾逗号 | 无 |
| 行宽 | 100 字符 |
| Svelte 插件 | `prettier-plugin-svelte` |
