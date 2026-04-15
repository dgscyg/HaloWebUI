# 认证系统概览

## 1. 身份

- **项目定义**: HaloWebUI 认证系统是一个多策略身份验证与授权框架，支持 JWT、OAuth、LDAP、API Key 等多种认证方式。
- **核心目标**: 为 Web 界面和 API 提供统一的身份验证入口，支持企业级单点登录集成和细粒度权限控制。

## 2. 支持的认证方式

### 2.1 本地认证 (邮箱密码)

- 使用 bcrypt 算法对密码进行哈希存储
- 支持用户自主注册（可配置开关）
- 首位注册用户自动成为管理员

### 2.2 访客访问 (Guest)

- 通过 `ENABLE_GUEST_ACCESS` 控制是否允许游客进入 Web 界面
- 通过 `GUEST_ACCESS_MODE` 控制登录页行为: `button` 显示“Continue As Guest”按钮，`auto` 直接进入游客会话
- 游客会话创建随机 `@guest.local` 本地账号，JWT 载荷带 `guest=true`
- 游客用户自动加入 `Guest` 用户组，便于统一做权限和资源范围管理

### 2.3 OAuth/OIDC 提供商

| 提供商    | 配置前缀                                 | 说明                 |
| --------- | ---------------------------------------- | -------------------- |
| Google    | `GOOGLE_OAUTH_*`                         | 支持 OpenID Connect  |
| Microsoft | `MICROSOFT_OAUTH_*`                      | 支持 Azure AD 集成   |
| GitHub    | `GITHUB_OAUTH_*`                         | 支持公开/私有邮箱    |
| 飞书      | `FEISHU_*`                               | 企业内部应用集成     |
| 通用 OIDC | `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET` | 兼容任意 OIDC 提供商 |

### 2.4 LDAP 认证

- 支持 TLS 加密连接
- 可配置用户属性映射 (邮箱、用户名)
- 支持用户组同步 (`ENABLE_LDAP_GROUP_SYNC`)
- 配置项: `LDAP_SERVER_HOST`, `LDAP_SEARCH_BASE`, `LDAP_APP_DN` 等

### 2.5 可信头部认证

- 通过 HTTP 头传递可信邮箱 (`WEBUI_AUTH_TRUSTED_EMAIL_HEADER`)
- 适用于反向代理前置认证场景
- 可配置用户名头部 (`WEBUI_AUTH_TRUSTED_NAME_HEADER`)

### 2.6 API Key 认证

- 格式: `sk-{uuid}` 前缀
- 支持端点访问限制 (`ENABLE_API_KEY_ENDPOINT_RESTRICTIONS`)
- 每个用户可生成独立的 API Key

## 3. 安全模型

### 3.1 Token 机制

- **算法**: JWT HS256 签名
- **密钥**: `WEBUI_SECRET_KEY` 环境变量
- **存储**: HTTP-Only Cookie + 可选 Bearer Header
- **过期**: 可配置 (`JWT_EXPIRES_IN`)，默认永不过期 (`-1`)
- **会话标识**: Token 包含 `jti` 字段用于多设备会话追踪

### 3.2 用户角色

| 角色      | 说明                       |
| --------- | -------------------------- |
| `admin`   | 系统管理员，拥有所有权限   |
| `user`    | 普通用户，受权限配置约束   |
| `pending` | 待审核用户，无系统访问权限 |

### 3.3 权限结构

权限采用嵌套字典结构，默认权限定义于 `backend/open_webui/config.py:1538-1574`:

```python
DEFAULT_USER_PERMISSIONS = {
    "workspace": {"models": False, "knowledge": False, "prompts": False, "tools": False},
    "chat": {"controls": True, "file_upload": True, "delete": True, "edit": True, "temporary": True},
    "features": {"web_search": True, "image_generation": True, "code_interpreter": True},
    ...
}
```

### 3.4 OAuth 安全特性

- 支持角色和组的自动同步 (`ENABLE_OAUTH_ROLE_MANAGEMENT`, `ENABLE_OAUTH_GROUP_MANAGEMENT`)
- 域名白名单限制 (`OAUTH_ALLOWED_DOMAINS`)
- 支持 PKCE (`OAUTH_CODE_CHALLENGE_METHOD`)
- 支持 RFC 8693 Token 交换 (`ENABLE_OAUTH_TOKEN_EXCHANGE`)
