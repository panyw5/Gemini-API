# 多 Cookies 轮询功能使用指南

## 概述

Gemini API 服务器现在支持多个 Google 账户的 cookies 轮询功能，实现负载均衡和容错处理。当一个账户达到速率限制或出现错误时，系统会自动切换到其他可用账户。

## 功能特性

- ✅ **多账户支持**: 支持配置多个 Google 账户的 cookies
- ✅ **负载均衡**: 支持轮询、随机、最少使用等策略
- ✅ **容错处理**: 自动检测失效账户并切换到可用账户
- ✅ **状态监控**: 提供 cookies 状态查看端点
- ✅ **向后兼容**: 完全兼容单 cookie 配置

## 配置方式

### 方式一：单个 Cookie（向后兼容）

在 `.env` 文件中配置单个账户：

```bash
SECURE_1PSID="your_secure_1psid_cookie_value"
SECURE_1PSIDTS="your_secure_1psidts_cookie_value"
```

### 方式二：多个独立环境变量（推荐）

在 `.env` 文件中配置多个账户：

```bash
# 账户 1
COOKIE_1_PSID="account1_secure_1psid_value"
COOKIE_1_PSIDTS="account1_secure_1psidts_value"
COOKIE_1_NAME="Account 1"

# 账户 2
COOKIE_2_PSID="account2_secure_1psid_value"
COOKIE_2_PSIDTS="account2_secure_1psidts_value"
COOKIE_2_NAME="Account 2"

# 账户 3
COOKIE_3_PSID="account3_secure_1psid_value"
COOKIE_3_PSIDTS="account3_secure_1psidts_value"
COOKIE_3_NAME="Account 3"
```

### 方式三：JSON 格式（高级用法）

在 `.env` 文件中使用 JSON 格式：

```bash
COOKIES_JSON='[
  {
    "secure_1psid": "account1_secure_1psid_value",
    "secure_1psidts": "account1_secure_1psidts_value",
    "name": "Primary Account"
  },
  {
    "secure_1psid": "account2_secure_1psid_value",
    "secure_1psidts": "account2_secure_1psidts_value",
    "name": "Secondary Account"
  }
]'
```

## 负载均衡策略

系统支持以下负载均衡策略：

1. **轮询（Round Robin）** - 默认策略，按顺序轮流使用账户
2. **随机（Random）** - 随机选择可用账户
3. **最少使用（Least Used）** - 选择最近最少使用的账户

## 容错机制

- 当账户出现 3 次连续错误时，会被标记为不可用
- 系统会自动切换到其他可用账户
- 成功请求会重置错误计数并恢复账户可用状态

## API 端点

### 查看 Cookies 状态

```bash
GET /cookies/status
```

返回示例：
```json
{
  "total_cookies": 3,
  "available_cookies": 2,
  "cookies": [
    {
      "name": "Account 1",
      "is_available": true,
      "error_count": 0,
      "last_used": 1672531200
    },
    {
      "name": "Account 2",
      "is_available": false,
      "error_count": 3,
      "last_used": 1672531100
    }
  ]
}
```

## 使用示例

### 启动服务

```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用启动脚本
./start.sh
```

### 测试多 Cookies 功能

```bash
# 运行测试脚本
python3 test_multi_cookies.py

# 查看 cookies 状态
curl http://localhost:50014/cookies/status

# 测试 API
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 获取 Google Cookies

1. 访问 https://gemini.google.com 并登录
2. 按 F12 打开开发者工具
3. 转到 Network 标签页并刷新页面
4. 点击任意请求，在 Headers 中找到 Cookie
5. 复制 `__Secure-1PSID` 和 `__Secure-1PSIDTS` 的值

## 最佳实践

1. **使用多个账户**: 建议配置 2-3 个不同的 Google 账户
2. **定期更新 Cookies**: Google cookies 会定期过期，需要及时更新
3. **监控状态**: 定期检查 `/cookies/status` 端点了解账户状态
4. **合理使用**: 遵守 Google 的使用条款，避免过度请求

## 故障排除

### 常见问题

1. **所有账户都不可用**
   - 检查 cookies 是否过期
   - 验证 cookies 格式是否正确
   - 确认网络连接正常

2. **某个账户频繁失效**
   - 可能达到了速率限制
   - 检查账户是否被暂时封禁
   - 尝试更新该账户的 cookies

3. **配置不生效**
   - 确认 `.env` 文件格式正确
   - 重启服务以加载新配置
   - 检查环境变量是否正确设置

### 日志查看

```bash
# 查看 Docker 日志
docker-compose logs -f

# 查看启动日志
tail -f logs/api_server.log
```

## 技术实现

- **CookieManager**: 管理多个 cookies 的核心类
- **CookieConfig**: 单个 cookie 配置和状态管理
- **负载均衡**: 支持多种选择策略
- **容错处理**: 自动错误检测和恢复机制
- **状态监控**: 实时状态报告和健康检查
