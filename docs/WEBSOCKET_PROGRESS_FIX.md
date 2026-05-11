# WebSocket 进度显示问题修复文档

## 问题描述

在 AI 对话页面（Chat.vue）提交 Crew 生成任务后，前端无法显示后端推送的实时进度更新。用户只能看到"后台正在生成 Crew，请稍候..."的初始消息，但看不到具体的进度步骤（如"生成项目主题"、"规划任务"等）。

## 问题表现

### 前端表现
- 页面只显示初始消息，没有进度更新
- 浏览器控制台显示 WebSocket 连接超时错误
- 错误信息：`WebSocket connection to 'ws://localhost:5173/api/chat/ws/xxx' failed`

### 后端表现
- 后端日志显示：`⚠️ No WebSocket connections for execution xxx, skipping progress message`
- 后端正常执行任务并生成结果，但无法推送进度给前端

## 根本原因分析

### 原因 1：Vite 代理未启用 WebSocket 支持 ⭐ **主要原因**

**问题**：前端通过 Vite 开发服务器（localhost:5173）访问后端 API（localhost:8000），但 Vite 的代理配置缺少 `ws: true` 选项，导致 WebSocket 连接无法通过代理转发。

**影响**：前端尝试连接 `ws://localhost:5173/api/chat/ws/xxx`，但 Vite 代理拒绝了 WebSocket 升级请求，连接立即失败。

**文件**：`frontend/vite.config.ts`

**修复前**：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      // ❌ 缺少 ws: true
    },
  },
}
```

**修复后**：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      ws: true,  // ✅ 启用 WebSocket 代理
    },
  },
}
```

---

### 原因 2：Vue 响应式问题

**问题**：进度消息对象 `logMessage` 是普通 JavaScript 对象，修改其属性（`logMessage.text += ...`）不会触发 Vue 的响应式更新，导致页面不重新渲染。

**影响**：即使 WebSocket 成功接收消息并更新了 `logMessage.text`，页面也不会显示新内容。

**文件**：`frontend/src/views/Chat.vue`

**修复前**：
```typescript
const logMessage = {
  role: 'assistant' as const,
  text: '🤖 后台正在生成 Crew，请稍候...\n\n',
  isGenerating: true
}
messages.value.push(logMessage)

// WebSocket 回调
onProgress: (data) => {
  logMessage.text += `${data.message}\n`  // ❌ 不会触发响应式更新
}
```

**修复后**：
```typescript
import { reactive } from 'vue'

const logMessage = reactive({  // ✅ 使用 reactive 包装
  role: 'assistant' as const,
  text: '🤖 后台正在生成 Crew，请稍候...\n\n',
  isGenerating: true
})
messages.value.push(logMessage)

// WebSocket 回调
onProgress: (data) => {
  logMessage.text += `${data.message}\n`  // ✅ 触发响应式更新
}
```

---

### 原因 3：后端延迟等待 WebSocket 连接

**问题**：后端使用 `BackgroundTasks.add_task()` 提交任务后，任务立即在后台开始执行并发送进度消息。但前端需要先收到 HTTP 响应，然后才能连接 WebSocket，存在时间差。

**影响**：前端错过了任务开始阶段的进度消息。

**文件**：`crewai_web/web/services/crew_generation_pipeline.py`

**修复**：
```python
import asyncio

async def execute(self, execution_id: str, scenario: str, doc_filenames: Optional[list[str]] = None):
    execution_log_service.update_status(execution_id, ExecutionStatus.RUNNING)
    
    # ✅ 等待 1 秒，让前端有时间连接 WebSocket
    logger.info(f"[Pipeline] Waiting 1s for WebSocket connection...")
    await asyncio.sleep(1.0)
    
    # 开始执行任务...
```

---

## 修复内容总结

### 1. 前端修复

#### 文件：`frontend/vite.config.ts`
- **修改**：在代理配置中添加 `ws: true`
- **原因**：启用 WebSocket 代理支持

#### 文件：`frontend/src/views/Chat.vue`
- **修改 1**：导入 `reactive` 并用它包装 `logMessage`
- **修改 2**：添加 `Message` 接口的 `isGenerating` 字段
- **原因**：确保进度消息的响应式更新

#### 文件：`frontend/src/composables/useWebSocket.ts`
- **修改**：添加连接超时检测（5秒）
- **原因**：快速发现连接失败问题

### 2. 后端修复

#### 文件：`crewai_web/web/services/crew_generation_pipeline.py`
- **修改**：导入 `asyncio` 并在 Pipeline 开始前等待 1 秒
- **原因**：给前端足够时间建立 WebSocket 连接

---

## 工作流程（修复后）

```
1. 用户提交任务
   ↓
2. 前端发送 POST /api/chat/generate-crew
   ↓
3. 后端创建 execution_id，启动后台任务，返回响应
   ↓
4. 前端收到 execution_id
   ↓
5. 前端立即连接 WebSocket (ws://localhost:5173/api/chat/ws/xxx)
   ↓
6. Vite 代理转发到后端 (ws://localhost:8000/api/chat/ws/xxx)
   ↓
7. 后端接受 WebSocket 连接
   ↓
8. 后台任务等待 1 秒（确保 WebSocket 已连接）
   ↓
9. 后台任务开始执行，发送进度消息
   ↓
10. 前端接收消息，更新 reactive 对象
   ↓
11. Vue 检测到响应式变化，重新渲染页面
   ↓
12. 用户看到实时进度更新 ✅
```

---

## 验证步骤

### 1. 重启前端服务器
```bash
cd frontend
npm run dev
```

### 2. 确保后端运行
```bash
python -m crewai_web.web
```

### 3. 测试
1. 打开浏览器访问 http://localhost:5173
2. 进入 AI 对话页面
3. 输入场景描述并提交
4. 观察页面是否显示实时进度

### 4. 预期结果
页面应该显示：
```
🤖 后台正在生成 Crew，请稍候...

⏳ 生成项目主题... (14%)
✅ 生成项目主题 完成 (14%)
⏳ 规划任务... (28%)
✅ 规划任务 完成 (28%)
⏳ 匹配 Agents... (42%)
✅ 匹配 Agents 完成 (42%)
⏳ 创建 Crew... (57%)
✅ 创建 Crew 完成 (57%)
⏳ 创建 Tasks... (71%)
✅ 创建 Tasks 完成 (71%)
⏳ 分配模型... (85%)
✅ 分配模型 完成 (85%)
⏳ 验证配置... (100%)
✅ 验证配置 完成 (100%)
```

---

## 技术要点

### WebSocket 代理配置
在使用 Vite 等开发服务器时，如果后端和前端在不同端口，必须在代理配置中显式启用 WebSocket 支持：
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    ws: true,  // ⭐ 必需
  }
}
```

### Vue 3 响应式原理
- 使用 `ref()` 包装的**基本类型**是响应式的
- 使用 `ref()` 包装的**对象**，修改对象属性**不会**触发更新
- 使用 `reactive()` 包装的对象，修改属性**会**触发更新
- 或者使用 `ref()` 并整体替换对象：`obj.value = { ...obj.value, text: newText }`

### WebSocket 连接时机
在使用后台任务（BackgroundTasks）时，需要考虑 WebSocket 连接建立的时间：
1. **方案 1**：后端延迟执行（本次采用）
2. **方案 2**：前端先连接 WebSocket，再提交任务（需要改变 API 设计）
3. **方案 3**：使用消息队列缓存早期消息

---

## 相关文件

### 修改的文件
- `frontend/vite.config.ts` - 启用 WebSocket 代理
- `frontend/src/views/Chat.vue` - 修复响应式问题
- `frontend/src/composables/useWebSocket.ts` - 添加超时检测
- `crewai_web/web/services/crew_generation_pipeline.py` - 添加延迟等待

### 架构文档
- `docs/CREW_GENERATION_ARCHITECTURE.md` - Crew 生成架构说明

---

## 常见问题

### Q: 为什么需要等待 1 秒？
A: 因为前端需要先收到 HTTP 响应获取 `execution_id`，然后才能建立 WebSocket 连接。1 秒的延迟确保连接已建立。

### Q: 能否缩短等待时间？
A: 可以，但需要确保网络延迟较低。建议保持 0.5-1 秒。

### Q: 如果 WebSocket 连接失败怎么办？
A: 前端会在 5 秒后超时并显示错误消息。用户可以查看控制台获取详细错误信息。

### Q: 生产环境需要修改吗？
A: 生产环境通常使用 Nginx 等反向代理，需要确保代理配置支持 WebSocket 升级：
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 修复日期
2026-05-11

## 修复人员
Cascade AI Assistant
