# WebSocket 连接故障排查指南

## 🚨 问题症状

WebSocket 连接失败，浏览器控制台显示：
```
[WebSocket] Error: Event {isTrusted: true, type: 'error', ...}
[WebSocket] Disconnected: 1006
[WebSocket] Reconnecting in 3 seconds...
```

---

## 🔍 原因分析

错误码 **1006** 表示异常关闭，常见原因：

1. **后端代码未部署** - 生产服务器还在运行旧代码
2. **认证失败** - `verify_player_token` 函数不存在或配置错误
3. **Nginx 配置问题** - WebSocket 升级未正确配置
4. **环境变量缺失** - JWT_SECRET_KEY 未设置

---

## ✅ 快速修复步骤

### 步骤 1: 在生产服务器上部署最新代码

```bash
# SSH 登录到服务器
ssh user@werewolf.newstardev.de

# 进入项目目录
cd /path/to/Werewolf

# 执行自动化部署脚本
chmod +x deploy.sh
./deploy.sh
```

**或手动执行**：

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 3. 查看日志确认启动成功
docker-compose logs -f backend
```

### 步骤 2: 运行诊断脚本

```bash
chmod +x diagnose-websocket.sh
./diagnose-websocket.sh
```

### 步骤 3: 检查环境配置

确保 `.env` 文件包含：

```env
# JWT 配置（必需）
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# CORS 配置（生产环境必须设置具体域名）
CORS_ORIGINS=https://werewolf.newstardev.de

# 调试模式（生产环境应为 false）
DEBUG=false
```

---

## 🧪 测试 WebSocket 连接

### 使用浏览器开发者工具

1. 打开 Chrome DevTools → Network → WS 标签
2. 刷新页面
3. 查看 WebSocket 连接状态：
   - **101 Switching Protocols** = 成功
   - **4xx/5xx** = 认证或服务器错误

### 使用 wscat 测试

```bash
# 安装 wscat
npm install -g wscat

# 测试连接（替换 YOUR_JWT_TOKEN）
wscat -c "wss://werewolf.newstardev.de/api/ws/game/test-game-id?token=YOUR_JWT_TOKEN"
```

---

## 📊 常见错误及解决方案

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| **1006** | 异常关闭 | 检查后端日志，重新部署代码 |
| **1008** | 策略违规 | JWT 认证失败，检查 token |
| **1005** | 无状态码 | 网络问题或服务器崩溃 |
| **1000** | 正常关闭 | 检查为何立即关闭，可能是验证失败 |

---

## 🔧 高级故障排查

### 1. 检查后端日志

```bash
# 查看最近 100 行日志
docker-compose logs --tail=100 backend

# 实时查看日志
docker-compose logs -f backend

# 过滤 WebSocket 相关日志
docker-compose logs backend | grep -i "websocket\|ws.*error"
```

### 2. 验证认证模块

```bash
# 进入后端容器
docker-compose exec backend bash

# 测试导入
python -c "from app.core.auth import verify_player_token; print('OK')"
```

### 3. 检查 Nginx 配置

确保 `frontend/nginx.conf` 包含 WebSocket 升级配置：

```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_cache_bypass $http_upgrade;
    # ... 其他配置
}
```

### 4. 清理并重建

```bash
# 完全清理（注意：会删除所有容器和卷）
docker-compose down -v
docker system prune -f

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

---

## 📞 仍然无法解决？

1. **收集诊断信息**：
   ```bash
   ./diagnose-websocket.sh > diagnostic-report.txt
   docker-compose logs backend > backend-logs.txt
   ```

2. **检查 GitHub Issues**：
   https://github.com/NewstarDevelop/Werewolf/issues

3. **查看最新提交**：
   - `aee9843` - WebSocket 管理器重构
   - `bee0cc0` - 端点认证修复
   - `ce131f7` - 前端状态合并

---

## ✨ 成功标志

部署成功后，浏览器控制台应显示：

```
[WebSocket] Connecting to: wss://werewolf.newstardev.de/api/ws/game/...
[WebSocket] Connected to game <game_id>
[WebSocket] Received message: connected
```

不再出现 1006 错误和无限重连！
