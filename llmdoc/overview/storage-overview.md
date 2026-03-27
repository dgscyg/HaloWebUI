# 数据存储概览

## 1. Identity

- **What it is:** HaloWebUI 的数据持久化层，包含关系型数据库和文件存储两大子系统。
- **Purpose:** 为应用提供可靠的数据持久化能力，支持从单机 SQLite 到生产级 PostgreSQL 的平滑迁移，以及本地到云端存储的无缝切换。

## 2. High-Level Description

HaloWebUI 采用双层数据存储架构：

**数据库层：**
- 默认使用 SQLite，适合单机部署和开发测试
- 支持 PostgreSQL，适合生产环境多实例部署
- 支持 SQLCipher 加密，提供数据库级别的安全保护
- 使用 SQLAlchemy ORM 进行数据访问，Pydantic 进行数据验证

**文件存储层：**
- 抽象存储接口 `StorageProvider`，支持四种后端实现
- 本地存储（默认）：文件存储在 `DATA_DIR/uploads/` 目录
- 云存储：支持 AWS S3、Google Cloud Storage、Azure Blob Storage
- 通过 `STORAGE_PROVIDER` 环境变量一键切换存储后端

**迁移系统：**
- Peewee 迁移：遗留迁移脚本，用于旧版兼容
- Alembic 迁移：主要迁移工具，管理数据库 Schema 演进
- 运行时迁移：自动检测并迁移 OpenWebUI 旧版数据库
