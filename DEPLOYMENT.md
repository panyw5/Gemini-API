# Gemini API Server 部署指南

本指南将帮助您通过 Docker 部署 Gemini API 服务器，提供 OpenAI 兼容的 API 接口来访问 Google Gemini 模型。

## 🚀 快速开始

### 1. 获取 Google Cookies

1. 访问 [https://gemini.google.com](https://gemini.google.com) 并登录您的 Google 账户
2. 按 F12 打开开发者工具，切换到 **Network** 标签页
3. 刷新页面
4. 点击任意请求，在 Headers 中找到 Cookie 部分
5. 复制 `__Secure-1PSID` 和 `__Secure-1PSIDTS` 的值

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的 cookie 值
nano .env
```

在 `.env` 文件中设置：
```bash
SECURE_1PSID=您的__Secure-1PSID值
SECURE_1PSIDTS=您的__Secure-1PSIDTS值
```

### 3. 一键启动

```bash
# 使用启动脚本（推荐）
./start.sh

# 或者手动启动
docker-compose up -d --build
```

### 4. 验证部署

```bash
# 检查服务健康状态
curl http://localhost:50014/health

# 查看可用模型
curl http://localhost:50014/v1/models

# 测试聊天接口
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 📋 可用模型

| 模型名称 | 描述 | 限制 |
|---------|------|------|
| `gemini-2.5-pro` | Gemini 2.5 Pro | 每日使用限制 |
| `gemini-2.5-flash` | Gemini 2.5 Flash | 无特殊限制 |
| `gemini-2.0-flash` | Gemini 2.0 Flash | 已弃用 |
| `gemini-2.0-flash-thinking` | Gemini 2.0 Flash Thinking | 已弃用 |
| `gemini-2.5-exp-advanced` | Gemini 2.5 实验高级版 | 需要 Gemini Advanced 订阅 |
| `gemini-2.0-exp-advanced` | Gemini 2.0 实验高级版 | 需要 Gemini Advanced 订阅 |

## 🔧 API 接口

### 获取模型列表

```bash
GET /v1/models
```

### 聊天完成（非流式）

```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gemini-2.5-flash",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

### 聊天完成（流式）

```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gemini-2.5-flash",
  "messages": [
    {"role": "user", "content": "Tell me a story"}
  ],
  "stream": true
}
```

## 💻 客户端使用示例

### Python (OpenAI 库)

```python
import openai

client = openai.OpenAI(
    api_key="dummy",  # 不使用但必需
    base_url="http://localhost:50014/v1"
)

response = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=[
        {"role": "user", "content": "你好！"}
    ]
)

print(response.choices[0].message.content)
```

### Node.js

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'dummy',
  baseURL: 'http://localhost:50014/v1',
});

const response = await openai.chat.completions.create({
  model: 'gemini-2.5-flash',
  messages: [{ role: 'user', content: '你好！' }],
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl -X POST http://localhost:50014/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "你好！"}
    ]
  }'
```

## 🛠️ 管理命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build

# 运行测试
python test_api.py
```

## 🔍 故障排除

### 常见问题

1. **认证错误**
   - 确保 cookies 有效且未过期
   - 尝试重新获取 cookies

2. **模型不可用**
   - 某些模型需要 Gemini Advanced 订阅
   - 检查模型名称是否正确

3. **速率限制**
   - Gemini Pro 模型有每日使用限制
   - 尝试使用 Flash 模型

### 日志查看

```bash
# 查看容器日志
docker-compose logs -f gemini-api

# 查看健康状态
curl http://localhost:50014/health
```

### Cookie 刷新

如果遇到认证问题：

1. 清除浏览器中 gemini.google.com 的缓存
2. 重新登录 https://gemini.google.com
3. 获取新的 cookie 值
4. 更新 `.env` 文件
5. 重启容器：`docker-compose restart`

## 📁 项目结构

```
.
├── api_server.py           # FastAPI 服务器
├── Dockerfile             # Docker 镜像配置
├── docker-compose.yml     # Docker Compose 配置
├── .env.example           # 环境变量模板
├── start.sh              # 启动脚本
├── test_api.py           # API 测试脚本
├── examples/             # 使用示例
│   ├── openai_client_example.py
│   └── curl_examples.sh
├── src/gemini_webapi/    # Gemini Web API 客户端
└── README_API.md         # API 文档
```

## 🔒 安全注意事项

1. **Cookie 安全**：不要在公共场所或不安全的网络中使用
2. **访问控制**：在生产环境中添加适当的访问控制
3. **HTTPS**：在生产环境中使用 HTTPS
4. **防火墙**：限制对 API 端口的访问

## 📈 性能优化

1. **资源限制**：在 docker-compose.yml 中调整内存和 CPU 限制
2. **并发处理**：根据需要调整 uvicorn 的 worker 数量
3. **缓存**：考虑添加响应缓存机制

## 🆘 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查健康状态：`curl http://localhost:50014/health`
3. 运行测试：`python test_api.py`
4. 查看原项目文档：[Gemini-API](https://github.com/HanaokaYuzu/Gemini-API)

## 📄 许可证

本项目使用与原 Gemini-API 项目相同的许可证。
