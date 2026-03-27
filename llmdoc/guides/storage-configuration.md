# 如何配置存储

本指南介绍如何配置 HaloWebUI 的数据库和文件存储。

## 1. 数据库配置

### SQLite (默认)

无需配置，自动使用 `{DATA_DIR}/webui.db`。

```bash
# 可选：SQLCipher 加密
DATABASE_ENCRYPTION_KEY=your-encryption-key
```

### PostgreSQL

```bash
DATABASE_URL=postgresql://user:password@host:5432/database_name

# 可选：连接池配置
DATABASE_POOL_SIZE=10
DATABASE_POOL_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# 可选：Schema (PostgreSQL)
DATABASE_SCHEMA=my_schema
```

## 2. 文件存储配置

### 本地存储 (默认)

```bash
STORAGE_PROVIDER=local
# 文件存储在 {DATA_DIR}/uploads/
```

### AWS S3 或兼容服务

```bash
STORAGE_PROVIDER=s3
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION_NAME=us-east-1
S3_BUCKET_NAME=your-bucket

# 可选配置
S3_ENDPOINT_URL=https://s3.example.com  # 非 AWS 服务
S3_KEY_PREFIX=openwebui/  # 对象前缀
S3_USE_ACCELERATE_ENDPOINT=false
S3_ADDRESSING_STYLE=auto
```

### Google Cloud Storage

```bash
STORAGE_PROVIDER=gcs
GCS_BUCKET_NAME=your-bucket

# 认证方式一：JSON 凭证
GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'

# 认证方式二：自动检测环境凭证（GCE/GKE）
# 不设置 GOOGLE_APPLICATION_CREDENTIALS_JSON，使用实例元数据服务
```

### Azure Blob Storage

```bash
STORAGE_PROVIDER=azure
AZURE_STORAGE_ENDPOINT=https://youraccount.blob.core.windows.net
AZURE_STORAGE_CONTAINER_NAME=your-container

# 认证方式一：存储密钥
AZURE_STORAGE_KEY=your-storage-key

# 认证方式二：Managed Identity
# 不设置 AZURE_STORAGE_KEY，使用 DefaultAzureCredential
```

## 3. 验证配置

1. **检查数据库连接：** 启动应用，观察日志中数据库初始化信息。
2. **测试文件上传：** 上传一个文件，检查存储位置是否符合预期。
3. **日志级别：** 设置 `DB_LOG_LEVEL=DEBUG` 查看详细数据库操作。

## 4. 注意事项

- 切换数据库类型后需要重新初始化或迁移数据
- 云存储需要安装对应的可选依赖：`pip install open-webui[storage-cloud]`
- SQLCipher 加密时连接池被禁用（`NullPool`），不适合高并发场景
