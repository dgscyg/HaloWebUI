# 如何添加新的前端组件/页面

本指南介绍如何在 HaloWebUI 前端中添加新的 Svelte 组件或页面路由。

## 1. 添加新的 UI 组件

1. **确定组件类型**: 根据功能域选择目录：
   - 通用组件: `src/lib/components/common/`
   - 聊天组件: `src/lib/components/chat/`
   - 布局组件: `src/lib/components/layout/`
   - 设置组件: `src/lib/components/settings/`

2. **创建组件文件**: 在选定目录下创建 `.svelte` 文件。
   ```svelte
   <!-- src/lib/components/common/MyComponent.svelte -->
   <script lang="ts">
     import { someStore } from '$lib/stores';
     export let myProp: string;
   </script>
   <div>{myProp}</div>
   ```

3. **导入使用**: 在需要的地方导入组件。
   ```svelte
   import MyComponent from '$lib/components/common/MyComponent.svelte';
   ```

## 2. 添加新的 API 模块

1. **创建 API 文件**: 在 `src/lib/apis/` 下创建新模块。
   ```typescript
   // src/lib/apis/myFeature/index.ts
   import { WEBUI_BASE_URL } from '$lib/constants';

   export const getMyData = async (token: string) => {
     const res = await fetch(`${WEBUI_BASE_URL}/api/my-feature`, {
       headers: { Authorization: `Bearer ${token}` }
     });
     return res.json();
   };
   ```

2. **统一认证**: 所有 API 请求使用 Bearer Token 认证。

## 3. 添加新页面路由

1. **确定路由类型**:
   - 需认证页面: 在 `src/routes/(app)/` 下创建
   - 公开页面: 在 `src/routes/` 下创建

2. **创建页面文件**: SvelteKit 使用文件系统路由。
   ```
   # 新增 /settings/my-feature 页面
   src/routes/(app)/settings/my-feature/+page.svelte
   ```

3. **页面组件示例**:
   ```svelte
   <script lang="ts">
     import { onMount } from 'svelte';
     import { user, config } from '$lib/stores';
     import { getMyData } from '$lib/apis/myFeature';

     onMount(async () => {
       if ($user) {
         const data = await getMyData(localStorage.token);
       }
     });
   </script>
   <div>My Feature Page</div>
   ```

4. **添加导航入口**: 在 `src/lib/components/layout/Sidebar.svelte` 或相关菜单组件中添加链接。

## 4. 添加新的全局状态

1. **打开 Store 文件**: 编辑 `src/lib/stores/index.ts`。

2. **添加 writable store**:
   ```typescript
   import { writable } from 'svelte/store';
   export const myNewState = writable<MyType>(initialValue);
   ```

3. **在组件中使用**:
   ```svelte
   <script>
     import { myNewState } from '$lib/stores';
     // 使用 $myNewState 进行响应式访问
   </script>
   <div>{$myNewState}</div>
   ```

## 5. 验证更改

1. **类型检查**: 运行 `npm run check` 确保无 TypeScript 错误。
2. **开发服务器**: 运行 `npm run dev` 启动开发服务器测试。
3. **构建测试**: 运行 `npm run build` 确保构建成功。

## 参考文档

- 组件架构: `/llmdoc/architecture/frontend-architecture.md`
- 项目概览: `/llmdoc/overview/frontend-overview.md`
