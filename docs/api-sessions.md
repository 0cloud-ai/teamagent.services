# Sessions API — 会话管理

> 会话的列表、详情、创建和对话。前端右侧面板的数据源。

---

## GET /api/v1/sessions/{path}

> 列出指定目录下的会话，支持游标分页和排序。

故事中的场景：林远舟点击 payment-gateway 目录，右侧显示 12 条会话。

```
GET /api/v1/sessions/home/linyuanzhou/payment-gateway?sort=updated_at&limit=20
```

```json
{
  "path": "/home/linyuanzhou/payment-gateway",
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "重构 PaymentProcessor 的回调逻辑",
      "created_at": "2026-03-23T14:30:00Z",
      "updated_at": "2026-03-23T17:45:00Z",
      "message_count": 47
    },
    {
      "id": "994c2844-c63f-85h8-e150-880099884444",
      "title": "修复支付回调签名校验",
      "created_at": "2026-03-21T10:00:00Z",
      "updated_at": "2026-03-21T16:20:00Z",
      "message_count": 34
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 12
  }
}
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cursor | string? | null | 上一页最后一条的 id |
| limit | int (1-100) | 20 | 每页条数 |
| sort | string | updated_at | 排序字段：`updated_at` 或 `created_at` |

**状态：** ✅ 已实现

---

## GET /api/v1/sessions/{session_id}/messages

> 获取单个会话的完整对话记录。

故事中的场景：
- 林远舟点进小王的会话，查看他改了什么（第四章）
- 林远舟点进自己三天前的会话，看到 47 条历史消息（第五章）

```
GET /api/v1/sessions/994c2844-c63f-85h8-e150-880099884444/messages?limit=50
```

```json
{
  "session_id": "994c2844-c63f-85h8-e150-880099884444",
  "session": {
    "id": "994c2844-c63f-85h8-e150-880099884444",
    "title": "修复支付回调签名校验",
    "path": "/home/linyuanzhou/payment-gateway",
    "created_at": "2026-03-21T10:00:00Z",
    "updated_at": "2026-03-21T16:20:00Z",
    "message_count": 34
  },
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "帮我排查一下回调接口收到异常签名的问题...",
      "created_at": "2026-03-21T10:00:00Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "我来看一下 `src/callback_handler.py`...",
      "created_at": "2026-03-21T10:00:12Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 34
  }
}
```

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cursor | string? | null | 上一页最后一条消息的 id |
| limit | int (1-100) | 50 | 每页条数 |
| order | string | asc | `asc`（从头看）或 `desc`（从最新看）|

**状态：** 🆕 需新增

---

## POST /api/v1/sessions/{path}

> 在指定目录下新建会话。

故事中的场景：林远舟要在 payment-gateway 目录下开一个全新的对话。

```
POST /api/v1/sessions/home/linyuanzhou/payment-gateway
```

```json
{
  "title": "添加退款异步重试机制"
}
```

**响应：**

```json
{
  "id": "aab91f00-d82e-4f5a-b123-abcdef123456",
  "title": "添加退款异步重试机制",
  "path": "/home/linyuanzhou/payment-gateway",
  "created_at": "2026-03-26T01:17:00Z",
  "updated_at": "2026-03-26T01:17:00Z",
  "message_count": 0
}
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 会话标题，不传则从第一条用户消息自动生成 |

**状态：** 🆕 需新增

---

## POST /api/v1/sessions/{session_id}/messages

> 在会话中发送一条消息，Agent 处理后流式返回响应。

故事中的场景：林远舟在输入框里敲下消息，Agent 读取文件、编辑代码、返回结果（第五章、第六章）。

```
POST /api/v1/sessions/550e8400-e29b-41d4-a716-446655440000/messages
```

```json
{
  "content": "我回来了。上次我们拆完了 callback_handler，但退款的部分还没做。注意：小王上周五改过 src/callback_handler.py 的签名校验逻辑，加了 URL decode 兼容，不要覆盖他的改动。现在需要在 RefundProcessor 里加一个异步重试机制，失败后按 1s、2s、4s 的间隔指数退避，最多重试 3 次。"
}
```

**响应（流式 SSE）：**

Agent 的响应通过 Server-Sent Events 流式返回，前端逐行渲染，实现"终端输出在浏览器里一行行地滚动"的体验。

```
Content-Type: text/event-stream

event: thinking
data: {"content": "让我先读取 src/refund_processor.py 的当前内容..."}

event: tool_use
data: {"tool": "read_file", "path": "src/refund_processor.py"}

event: text
data: {"content": "我看到了当前的 RefundProcessor 实现。接下来我会添加指数退避的重试机制..."}

event: tool_use
data: {"tool": "edit_file", "path": "src/refund_processor.py", "description": "添加异步重试逻辑"}

event: text
data: {"content": "重试机制已添加。来跑一遍单元测试确认没有回归..."}

event: tool_use
data: {"tool": "run_command", "command": "python -m pytest tests/test_refund.py"}

event: text
data: {"content": "所有测试通过 ✓\n\n修改总结：\n1. 新增 `_retry_with_backoff()` 方法..."}

event: done
data: {"message_id": "msg-069", "session_updated_at": "2026-03-26T02:14:00Z"}
```

**SSE 事件类型：**

| 事件 | 说明 |
|------|------|
| `thinking` | Agent 的思考过程 |
| `text` | Agent 的文本回复 |
| `tool_use` | Agent 调用工具（读文件、编辑文件、执行命令等）|
| `tool_result` | 工具执行结果 |
| `error` | 错误信息 |
| `done` | 本轮响应结束 |

**状态：** 🆕 需新增

---

## 响应模型

### Session

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话 ID（UUID）|
| title | string | 会话标题 |
| path | string | 所属目录路径 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |
| message_count | int | 消息总数 |

### Message

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息 ID |
| role | string | `user` 或 `assistant` |
| content | string | 消息内容 |
| created_at | datetime | 发送时间 |

### Pagination

| 字段 | 类型 | 说明 |
|------|------|------|
| next_cursor | string? | 下一页的游标，null 表示没有更多 |
| has_more | bool | 是否有下一页 |
| total | int | 符合条件的总数 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 404 | 路径不存在 / 会话不存在 |
| 400 | 参数校验失败（如 limit 超出范围）|

---

## 前端调用流程

```
用户点击目录 "payment-gateway"
  → GET /api/v1/sessions/home/linyuanzhou/payment-gateway

用户滚到底部点 "Load more"
  → GET /api/v1/sessions/home/linyuanzhou/payment-gateway?cursor=xxx

用户点击某条会话
  → GET /api/v1/sessions/550e8400.../messages

用户新建会话
  → POST /api/v1/sessions/home/linyuanzhou/payment-gateway

用户发送消息
  → POST /api/v1/sessions/550e8400.../messages
  → 前端通过 EventSource 接收 SSE 流，逐行渲染 Agent 响应
```
