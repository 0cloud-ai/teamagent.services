# Workspace — Service Inbox API

> 在工程面板中查看和管理来自服务面板的工单（conversation）。工单模型类似 GitHub Issue。

---

## 概念

服务面板的每个 conversation 就是一个**工单**。Workspace 成员可以：

- 查看所有工单及其状态和标签
- 上升（escalate）、关闭（close）、重新打开工单
- 更新标签
- 在任意 session 中 @引用工单，像引用附件一样

```
服务面板                          工程面板

conv-001 (open)       ←──查看──→  service inbox
conv-002 (escalated)              ├── 上升 / 关闭 / 打标签
conv-003 (closed)                 └── 在 session 中 @引用

                                 session-A: "参考 @conv-001 的需求，开始开发..."
                                 session-B: "@conv-002 这个问题我看了，是..."
```

工单不和 session 一一对应。一个工单可以被多个 session 引用，一个 session 也可以引用多个工单。

---

## 工单列表

### GET /api/v1/workspace/service-inbox

> 列出所有服务工单，支持按状态和标签过滤。

```
GET /api/v1/workspace/service-inbox?status=escalated
```

```json
{
  "conversations": [
    {
      "id": "conv-001",
      "title": "支付成功后发放优惠券",
      "consumer": { "user_id": "user-002", "name": "陈霜" },
      "status": "open",
      "labels": ["feature-request"],
      "created_at": "2026-03-26T09:30:00Z",
      "updated_at": "2026-03-26T09:45:00Z",
      "message_count": 6
    },
    {
      "id": "conv-002",
      "title": "退款流程异常，用户未收到退款",
      "consumer": { "user_id": "user-005", "name": "张伟" },
      "status": "escalated",
      "labels": ["bug", "payment"],
      "created_at": "2026-03-25T14:00:00Z",
      "updated_at": "2026-03-25T14:10:00Z",
      "message_count": 4
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 2
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | string? | null | `open`、`escalated`、`closed`，不传返回全部 |
| label | string? | null | 按标签过滤 |
| cursor | string? | null | 游标 |
| limit | int (1-100) | 20 | 每页条数 |

**状态：** 🆕 需新增

---

## 工单详情

### GET /api/v1/workspace/service-inbox/{conversation_id}

> 查看工单的完整对话记录。

```
GET /api/v1/workspace/service-inbox/conv-001
```

```json
{
  "id": "conv-001",
  "title": "支付成功后发放优惠券",
  "consumer": { "user_id": "user-002", "name": "陈霜" },
  "status": "open",
  "labels": ["feature-request"],
  "closed_at": null,
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "支付成功后给用户发一张优惠券，想了解一下技术上怎么实现，需要多久。",
      "created_at": "2026-03-26T09:30:00Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "好的，关于支付成功后发放优惠券，我需要确认几个细节...",
      "created_at": "2026-03-26T09:30:15Z"
    }
  ],
  "referenced_by": [
    {
      "session_id": "sess-abc",
      "session_title": "实现支付成功后发券功能"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 6
  }
}
```

`referenced_by` 列出哪些 session 引用了这个工单，方便追踪处理情况。

**状态：** 🆕 需新增

---

## 上升

### POST /api/v1/workspace/service-inbox/{conversation_id}/escalate

> 将工单标记为上升。Agent 自动触发或 workspace 成员手动触发。

```
POST /api/v1/workspace/service-inbox/conv-002/escalate
```

```json
{
  "reason": "涉及第三方支付渠道的接口限制，Agent 无法判断"
}
```

**响应：**

```json
{
  "id": "conv-002",
  "status": "escalated"
}
```

上升后，服务面板消费者会通过 SSE `status_changed` 事件感知到状态变化。

**状态：** 🆕 需新增

---

## 关闭

### POST /api/v1/workspace/service-inbox/{conversation_id}/close

> 关闭工单。

```
POST /api/v1/workspace/service-inbox/conv-001/close
```

**响应：**

```json
{
  "id": "conv-001",
  "status": "closed",
  "closed_at": "2026-03-26T15:00:00Z"
}
```

消费者侧同步更新。消费者后续发新消息会自动 reopen。

**状态：** 🆕 需新增

---

## 重新打开

### POST /api/v1/workspace/service-inbox/{conversation_id}/reopen

> 重新打开已关闭的工单。

```
POST /api/v1/workspace/service-inbox/conv-001/reopen
```

**响应：**

```json
{
  "id": "conv-001",
  "status": "open"
}
```

**状态：** 🆕 需新增

---

## 更新标签

### PUT /api/v1/workspace/service-inbox/{conversation_id}/labels

> 更新工单的标签。

```
PUT /api/v1/workspace/service-inbox/conv-001/labels
```

```json
{
  "labels": ["feature-request", "payment", "priority-high"]
}
```

**响应：**

```json
{
  "id": "conv-001",
  "labels": ["feature-request", "payment", "priority-high"]
}
```

**状态：** 🆕 需新增

---

## 在 Session 中引用工单

工单可以在任意 workspace session 的消息中被 @引用：

```
POST /api/v1/workspace/sessions/{session_id}/messages
```

```json
{
  "content": "参考 @conv-001 的需求，陈霜要的是支付成功后发 10 元优惠券。我们基于上次的代码改一下参数就行。",
  "mentions": ["conv-001"]
}
```

`mentions` 统一支持两种引用：

| ID 格式 | 类型 | 行为 |
|---------|------|------|
| `mem-xxx` | workspace member | @ 用户发通知，@ 外部服务发请求 |
| `conv-xxx` | service conversation | 引用工单内容，Agent 可读取工单上下文 |

当 session 引用了某个 conversation，该 session 会出现在工单详情的 `referenced_by` 列表中。

---

## 状态模型

与 service/conversations 的状态完全一致：

```
open ←──────→ escalated
  │                │
  ↓                ↓
closed ←───── closed
  │
  ↓ (消费者发新消息 或 workspace reopen)
open
```

| 从 | 到 | workspace 可触发 | 说明 |
|----|----|-----------------|------|
| `open` | `escalated` | ✅ escalate | 需要人工介入 |
| `open` | `closed` | ✅ close | 问题解决 |
| `escalated` | `open` | ✅ reopen | 降级回正常 |
| `escalated` | `closed` | ✅ close | 问题解决 |
| `closed` | `open` | ✅ reopen | 重新打开 |

---

## 响应模型

### InboxConversation

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | conversation ID |
| title | string | 工单标题 |
| consumer | ConsumerInfo | 发起者 |
| status | string | `open`、`escalated`、`closed` |
| labels | string[] | 标签列表 |
| closed_at | datetime? | 关闭时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |
| message_count | int | 消息数 |
| referenced_by | SessionRef[] | 引用该工单的 session 列表（仅详情返回）|

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 状态转换不合法 |
| 403 | 无权限 |
| 404 | 工单不存在 |
