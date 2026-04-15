# 存储架构

## 1. Identity

- **What it is:** HaloWebUI 数据持久化的技术实现架构。
- **Purpose:** 为开发者提供数据库模型、ORM 使用、迁移系统和文件存储的完整技术参考。

## 2. Core Components

### 数据库核心

- `backend/open_webui/internal/db.py` (Base, get_db, JSONField, handle_peewee_migration): SQLAlchemy 基类定义、会话管理、自定义 JSON 字段类型、Peewee 迁移入口。
- `backend/open_webui/env.py` (DATABASE_URL, DATABASE_POOL_SIZE, DATABASE_ENCRYPTION_KEY): 数据库连接配置和连接池参数环境变量。

### 数据模型 (17 个)

- `backend/open_webui/models/users.py` (User): 用户模型，包含认证信息和设置。
- `backend/open_webui/models/chats.py` (Chat, ChatMessage): 聊天和消息模型，实现 JSON 字段与独立消息表的双写。
- `backend/open_webui/models/files.py` (File): 文件元数据模型，存储路径、哈希和访问控制。
- `backend/open_webui/models/auths.py`, `groups.py`, `prompts.py`, `tools.py`, `functions.py`, `memories.py`, `folders.py`, `models.py`, `channels.py`, `skills.py`, `notes.py`, `knowledge.py`, `tags.py`: 其他业务模型。

### 文件存储

- `backend/open_webui/storage/provider.py` (StorageProvider, LocalStorageProvider, S3StorageProvider, GCSStorageProvider, AzureStorageProvider): 存储抽象接口和四种后端实现。
- `backend/open_webui/config.py:933-953` (STORAGE*PROVIDER, S3*\_, GCS\_\_, AZURE\_\*): 存储配置环境变量定义。

### 迁移系统

- `backend/open_webui/runtime_migrations.py` (ensure_runtime_migrated, \_detect_database): 运行时自动迁移，检测并迁移 OpenWebUI 旧版数据库。
- `backend/open_webui/migrations/versions/`: Alembic 迁移版本脚本目录（约 30 个文件）。
- `backend/open_webui/internal/migrations/`: Peewee 遗留迁移脚本目录（20 个文件）。

## 3. Execution Flow (LLM Retrieval Map)

### 数据库初始化流程

1. **配置加载:** `env.py` 读取 `DATABASE_URL` 等环境变量，默认 `sqlite:///{DATA_DIR}/webui.db`。
2. **Peewee 迁移:** `db.py:76-98` 的 `handle_peewee_migration()` 在 SQLAlchemy 初始化前执行遗留迁移。
3. **引擎创建:** `db.py:102-146` 根据 URL 类型创建引擎：
   - SQLite: 配置 WAL 模式、内存缓存等 PRAGMA
   - PostgreSQL: 配置连接池参数
   - SQLCipher: 使用 `pysqlcipher` 驱动并禁用连接池
4. **Alembic 迁移:** `config.py:78-93` 的 `run_migrations()` 执行 Alembic 升级。
5. **运行时迁移:** `runtime_migrations.py` 检测旧版数据库并自动迁移。

### 文件上传流程

1. **请求接收:** API 路由接收上传请求。
2. **存储路由:** `provider.py:396-414` 的 `get_storage_provider()` 根据 `STORAGE_PROVIDER` 选择实现。
3. **文件处理:** `LocalStorageProvider.upload_file()` 先写入本地临时文件。
4. **云端同步:** 云存储实现（如 `S3StorageProvider`）将临时文件上传到云端并返回云端路径。

### ORM 数据访问模式

```python
# 标准模式 (models/*.py)
from open_webui.internal.db import Base, get_db, JSONField

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(String, primary_key=True)
    data = Column(JSONField)  # 使用自定义 JSONField
    created_at = Column(BigInteger)  # Unix 时间戳

# 使用方式
with get_db() as db:
    items = db.query(MyModel).all()
```

## 4. Design Rationale

**双轨迁移机制：**

- Peewee 迁移仅用于向后兼容 OpenWebUI 旧版数据库
- 新功能开发统一使用 Alembic 迁移
- 运行时迁移自动处理版本升级，减少用户操作

**自定义 JSONField：**

- SQLAlchemy 的 JSON 类型在不同数据库间行为不一致
- 自定义 `JSONField` 确保跨数据库 JSON 兼容性

**存储抽象工厂模式：**

- 统一接口简化存储后端切换
- 云存储实现先写本地再同步，确保可靠性
- 依赖延迟加载，无云存储需求时不安装 boto3 等库
