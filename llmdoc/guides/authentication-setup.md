# 如何配置认证提供商

本指南介绍如何配置 HaloWebUI 支持的各种认证方式。

## 1. 配置本地认证

1. **设置基础认证**: 确保 `WEBUI_AUTH=true` (默认启用)
2. **配置注册开关**: 设置 `ENABLE_SIGNUP=true/false` 控制是否允许新用户注册
3. **设置默认角色**: 配置 `DEFAULT_USER_ROLE` 为 `user`、`admin` 或 `pending`
4. **验证**: 启动服务后访问 `/auth` 页面，应显示登录/注册表单

## 2. 配置 Google OAuth

1. **创建 OAuth 凭据**: 在 Google Cloud Console 创建 OAuth 2.0 客户端 ID
2. **设置环境变量**:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
3. **配置回调 URL**: 在 Google Console 中添加 `{YOUR_DOMAIN}/oauth/google/callback`
4. **可选配置**:
   - `GOOGLE_OAUTH_SCOPE=openid email profile` (默认值)
5. **验证**: 重启服务后，登录页面应显示 Google 登录按钮

## 3. 配置 Microsoft OAuth

1. **注册应用**: 在 Azure AD 中注册应用，获取 Application (client) ID
2. **设置环境变量**:
   ```bash
   MICROSOFT_CLIENT_ID=your-client-id
   MICROSOFT_CLIENT_SECRET=your-client-secret
   MICROSOFT_CLIENT_TENANT_ID=common  # 或 specific tenant ID
   ```
3. **配置回调 URL**: 添加 `{YOUR_DOMAIN}/oauth/microsoft/callback`
4. **验证**: 登录页面应显示 Microsoft 登录按钮

## 4. 配置 GitHub OAuth

1. **创建 OAuth App**: 在 GitHub Settings > Developer settings > OAuth Apps 创建新应用
2. **设置环境变量**:
   ```bash
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   ```
3. **配置回调 URL**: 设置 Authorization callback URL 为 `{YOUR_DOMAIN}/oauth/github/callback`
4. **验证**: 登录页面应显示 GitHub 登录按钮

## 5. 配置通用 OIDC

1. **获取提供商信息**: 从 OIDC 提供商获取 client_id、client_secret 和 well-known 配置 URL
2. **设置环境变量**:
   ```bash
   OAUTH_CLIENT_ID=your-client-id
   OAUTH_CLIENT_SECRET=your-client-secret
   OPENID_PROVIDER_URL=https://provider.example.com/.well-known/openid-configuration
   OAUTH_PROVIDER_NAME=SSO  # 显示名称
   ```
3. **可选高级配置**:
   - `OAUTH_USERNAME_CLAIM=name` - 用户名 claim 字段
   - `OAUTH_EMAIL_CLAIM=email` - 邮箱 claim 字段
   - `OAUTH_GROUPS_CLAIM=groups` - 组 claim 字段
   - `OAUTH_CODE_CHALLENGE_METHOD=S256` - PKCE 方法
4. **验证**: 登录页面应显示配置的 SSO 登录按钮

## 6. 配置 LDAP

1. **启用 LDAP**: 设置 `ENABLE_LDAP=true`
2. **配置服务器连接**:
   ```bash
   LDAP_SERVER_HOST=ldap.example.com
   LDAP_SERVER_PORT=389
   LDAP_USE_TLS=true
   LDAP_CA_CERT_FILE=/path/to/ca.crt  # 可选
   ```
3. **配置应用账户**:
   ```bash
   LDAP_APP_DN=cn=app,ou=users,dc=example,dc=com
   LDAP_APP_PASSWORD=app-password
   ```
4. **配置搜索参数**:
   ```bash
   LDAP_SEARCH_BASE=ou=users,dc=example,dc=com
   LDAP_ATTRIBUTE_FOR_MAIL=mail
   LDAP_ATTRIBUTE_FOR_USERNAME=uid
   LDAP_SEARCH_FILTERS=(objectClass=person)
   ```
5. **可选组同步**:
   ```bash
   ENABLE_LDAP_GROUP_SYNC=true
   LDAP_GROUP_ATTRIBUTE=memberOf
   ```
6. **验证**: 登录页面应显示 LDAP 登录表单，使用 LDAP 凭据测试登录

## 7. 配置可信头部认证

适用于反向代理前置认证场景 (如 OAuth2-Proxy, Authelia)。

1. **设置环境变量**:
   ```bash
   WEBUI_AUTH_TRUSTED_EMAIL_HEADER=X-Forwarded-Email
   WEBUI_AUTH_TRUSTED_NAME_HEADER=X-Forwarded-User  # 可选
   ```
2. **配置反向代理**: 确保代理在请求头中传递用户邮箱
3. **验证**: 通过代理访问时，系统应自动根据头部创建/登录用户

## 8. 配置 API Key 认证

1. **启用 API Key**: 在管理后台设置 `ENABLE_API_KEY=true`
2. **用户生成 Key**: 用户在设置页面点击生成 API Key (格式: `sk-xxx`)
3. **使用 API Key**:
   ```bash
   curl -H "Authorization: Bearer sk-xxx" http://localhost:8080/api/v1/models
   ```
4. **可选端点限制**:
   - `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS=true`
   - `API_KEY_ALLOWED_ENDPOINTS=/api/v1/models,/api/v1/chat`

## 9. 验证配置完成

1. 访问 `/admin/settings` 检查认证配置
2. 使用不同认证方式测试登录流程
3. 检查日志确认无认证错误 (`SRC_LOG_LEVELS.MAIN=DEBUG`)
