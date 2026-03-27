# 如何添加新的 API 端点

本指南介绍如何在 HaloWebUI 后端添加新的 REST API 端点。

## 1. 确定路由模块

根据功能域选择或创建路由文件:

| 功能域 | 路由文件 | 路径前缀 |
|--------|----------|----------|
| 用户相关 | `routers/users.py` | `/api/v1/users` |
| 聊天相关 | `routers/chats.py` | `/api/v1/chats` |
| 模型相关 | `routers/models.py` | `/api/v1/models` |
| 新功能域 | 创建新文件 | 自定义前缀 |

## 2. 定义数据模型 (如需)

如果需要新的数据表，在 `models/` 目录创建模型文件:

```
backend/open_webui/models/
├── your_model.py    # 新模型文件
```

模型文件结构:
- SQLAlchemy `Base` 类定义表结构
- Pydantic `BaseModel` 定义 DTO
- Table 类封装 CRUD 方法

参考: `backend/open_webui/models/users.py` (User, UsersTable)

## 3. 添加端点处理函数

在路由文件中添加端点:

```python
from fastapi import APIRouter, Depends, Request
from open_webui.utils.auth import get_verified_user

router = APIRouter()

@router.get("/your-endpoint")
async def get_your_data(
    request: Request,
    user=Depends(get_verified_user)  # 认证依赖
):
    # 业务逻辑
    return {"data": "your_response"}
```

认证依赖选项:
- `get_verified_user`: 需要已验证用户
- `get_admin_user`: 需要管理员权限
- `get_current_user`: 可选认证

参考: `backend/open_webui/routers/chats.py:15-50`

## 4. 注册路由

在 `main.py` 中注册新路由:

```python
from open_webui.routers import your_router

app.include_router(
    your_router.router,
    prefix="/api/v1/your-prefix",
    tags=["your-tag"]
)
```

参考: `backend/open_webui/main.py:1189-1226`

## 5. 添加配置项 (如需)

如果需要新配置项，在 `config.py` 中添加:

```python
# 环境变量读取
YOUR_CONFIG = PersistentConfig(
    "YOUR_CONFIG",
    "your.config.key",
    os.environ.get("YOUR_CONFIG", "default_value")
)

# 在 AppConfig 中注册
class AppConfig:
    YOUR_CONFIG: str = YOUR_CONFIG.value
```

然后在 `main.py` 中初始化:

```python
app.state.config.YOUR_CONFIG = YOUR_CONFIG
```

参考: `backend/open_webui/config.py` 和 `backend/open_webui/main.py:598-700`

## 6. 验证

1. 启动服务: `cd backend && python -m open_webui.main`
2. 访问 Swagger 文档: `http://localhost:8080/docs` (开发模式)
3. 测试端点: `curl -H "Authorization: Bearer <token>" http://localhost:8080/api/v1/your-endpoint`

## 示例: 添加导出端点

```python
# 在 routers/chats.py 中添加

from fastapi.responses import StreamingResponse

@router.get("/{chat_id}/export")
async def export_chat(
    chat_id: str,
    user=Depends(get_verified_user)
):
    """导出聊天记录为 JSON 文件"""
    chat = Chats.get_chat_by_id_and_user_id(chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    import json
    from io import BytesIO

    content = json.dumps(chat.chat, indent=2, ensure_ascii=False)
    return StreamingResponse(
        BytesIO(content.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=chat_{chat_id}.json"}
    )
```

## 相关文档

- 路由模块: `/llmdoc/architecture/backend-architecture.md`
- 认证系统: `/llmdoc/agent/scout-auth.md`
- 数据模型: `/llmdoc/agent/scout-storage.md`
