# 部署指南 - Claude Code Server API

## 📦 安装步骤

### 1. 克隆项目

```bash
cd /Users/eric/Project/viralt
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server
```

### 2. 安装依赖

```bash
# 方式 1: 完整安装（包含所有功能）
pip install -e ".[all]"

# 方式 2: 只安装 server
pip install -e ".[server]"

# 依赖包括:
# - fastapi: Web 框架
# - uvicorn: ASGI 服务器
# - pyyaml: 配置文件解析
# - sse-starlette: SSE 流式响应
# - redis: (可选) Redis session 存储
```

### 3. 创建工作目录

```bash
# 创建 Claude CLI 工作目录
mkdir -p /Users/eric/Project/viralt/claude-code-server-test-folder
cd /Users/eric/Project/viralt/claude-code-server-test-folder

# 初始化（可选，如果需要项目特定配置）
# claude init  # 这会创建 .claude 目录
```

### 4. 配置服务

```bash
cd /Users/eric/Project/viralt/claude-code-server

# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置
vim config.yaml
```

关键配置项：

```yaml
# 工作目录 - Claude CLI 运行的基础目录
working_directory: "/Users/eric/Project/viralt/claude-code-server-test-folder"

# Claude CLI 路径
claude_bin: "claude"  # 或 "/opt/homebrew/bin/claude"

# 响应模式
default_response_mode: "sync"  # sync/stream/async

# Session 存储
session_store_type: "memory"  # memory 或 redis
```

## 🚀 启动服务

### 开发环境

```bash
# 基本启动
python start_server.py

# 指定配置文件
python start_server.py --config config.yaml

# 开发模式（auto-reload）
python start_server.py --reload

# 自定义端口
python start_server.py --port 8080
```

### 生产环境

#### 方式 1: Uvicorn 直接运行

```bash
uvicorn claude_code_server_api.server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

#### 方式 2: Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn claude_code_server_api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 方式 3: Systemd Service

创建 `/etc/systemd/system/claude-api.service`:

```ini
[Unit]
Description=Claude Code Server API
After=network.target

[Service]
Type=notify
User=your-user
WorkingDirectory=/path/to/claude-code-server
Environment="PATH=/usr/local/bin"
ExecStart=/usr/bin/python3 start_server.py --config config.yaml
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable claude-api
sudo systemctl start claude-api
sudo systemctl status claude-api
```

## 🧪 测试服务

### 快速测试

```bash
# 健康检查
curl http://localhost:8000/health

# 简单聊天
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test"}'
```

### 完整测试套件

```bash
# 确保服务正在运行
python start_server.py &

# 运行测试
python test_api.py
```

## 🐳 Docker 部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

# 安装 Node.js (for Claude CLI)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic/claude-code \
    && apt-get clean

WORKDIR /app

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -e ".[all]"

# 创建工作目录
RUN mkdir -p /workspace

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "start_server.py", "--config", "config.yaml"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./workspace:/workspace
      - ./config.yaml:/app/config.yaml
    environment:
      - CLAUDE_WORKING_DIR=/workspace
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

运行：

```bash
docker-compose up -d
```

## 🔒 安全配置

### 1. API Key 认证

```yaml
# config.yaml
api_key: "your-super-secret-api-key-here"
```

客户端请求：

```bash
curl -H "X-API-Key: your-super-secret-api-key-here" \
  http://localhost:8000/chat
```

### 2. 限制用户

```yaml
# config.yaml
allowed_users:
  - "alice"
  - "bob"
  - "charlie"
```

### 3. CORS 配置

```yaml
# config.yaml
enable_cors: true
cors_origins:
  - "https://your-frontend.com"
  - "https://app.example.com"
```

### 4. HTTPS (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomaincom;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 监控

### 日志

服务日志输出到 stdout：

```bash
# 查看日志
journalctl -u claude-api -f

# Docker logs
docker-compose logs -f api
```

### 健康检查

```bash
# 定期检查
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart claude-api
```

## 🔧 故障排除

### 问题 1: Claude CLI not found

```bash
# 检查 Claude CLI 安装
which claude

# 如果没有找到，安装
npm install -g @anthropic/claude-code

# 配置中使用完整路径
claude_bin: "/opt/homebrew/bin/claude"
```

### 问题 2: 权限问题

```bash
# 确保工作目录可写
chmod 755 /Users/eric/Project/viralt/claude-code-server-test-folder

# 检查 Claude CLI 认证
claude --version
```

### 问题 3: Redis 连接失败

```bash
# 启动 Redis
redis-server

# 或使用 Docker
docker run -d -p 6379:6379 redis:7-alpine

# 测试连接
redis-cli ping
```

### 问题 4: 端口占用

```bash
# 查找占用进程
lsof -i :8000

# 使用其他端口
python start_server.py --port 8080
```

## 📈 性能优化

### 1. 增加 Workers

```bash
# 多个 worker 进程
python start_server.py --workers 4
```

### 2. Redis Session 存储

```yaml
session_store_type: "redis"
redis_url: "redis://localhost:6379"
```

### 3. 调整超时

```yaml
default_timeout: 600  # 10 分钟
task_timeout: 1200    # 20 分钟
```

---

**🎉 部署完成！现在你的 Claude Code Server API 已经可以对外服务了！**
