# Service — Conversations API

> 服务面板的对话管理。每个 conversation 是一个服务工单，模型类似 GitHub Issue。
>
> 工单数据统一存储在启动目录的 `.teamagent/conversations/` 下（见 [存储格式](../../context/conversations.md)），与目录结构无关。

---

## 对话列表

### GET /api/v1/service/conversations

> 列出当前消费者的所有对话。

```
GET /api/v1/service/conversations?status=open&limit=20
```

```json
{
  "conversations": [
    {
      "id": "conv-001",
      "title": "支付成功后发放优惠券",
      "status": "open",
      "labels": ["feature-request"],
      "created_at": "2026-03-26T09:30:00Z",
      "updated_at": "2026-03-26T15:00:00Z",
      "message_count": 24
    },
    {
      "id": "conv-002",
      "title": "退款流程异常，用户未收到退款",
      "status": "escalated",
      "labels": ["bug", "payment"],
      "created_at": "2026-03-25T14:00:00Z",
      "updated_at": "2026-03-25T14:10:00Z",
      "message_count": 4
    },
    {
      "id": "conv-003",
      "title": "退款流程技术可行性咨询",
      "status": "closed",
      "labels": ["question"],
      "closed_at": "2026-03-20T15:30:00Z",
      "created_at": "2026-03-20T14:00:00Z",
      "updated_at": "2026-03-20T15:30:00Z",
      "message_count": 8
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 3
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

## 新建对话

### POST /api/v1/service/conversations

> 发起一个新对话（工单）。初始状态为 `open`。

```
POST /api/v1/service/conversations
```

```json
{
  "message": "支付成功后给用户发一张优惠券，想了解一下技术上怎么实现，需要多久。",
  "labels": ["feature-request"]
}
```

**响应（流式 SSE）：**

```
Content-Type: text/event-stream

event: conversation_created
data: {"id": "conv-004", "title": "支付成功后发放优惠券", "status": "open"}

event: text
data: {"content": "好的，关于支付成功后发放优惠券，我需要确认几个细节：\n\n1. 优惠券类型：固定金额还是折扣？..."}

event: done
data: {"message_id": "msg-001", "conversation_updated_at": "2026-03-26T09:30:15Z"}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 第一条消息 |
| labels | string[] | 否 | 标签列表 |

**状态：** 🆕 需新增

---

## 对话详情

### GET /api/v1/service/conversations/{conversation_id}

> 获取对话完整信息和消息记录。

```
GET /api/v1/service/conversations/conv-001?limit=50
```

```json
{
  "id": "conv-001",
  "title": "支付成功后发放优惠券",
  "status": "open",
  "labels": ["feature-request"],
  "created_at": "2026-03-26T09:30:00Z",
  "updated_at": "2026-03-26T15:00:00Z",
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
      "content": "好的，关于支付成功后发放优惠券，我需要确认几个细节：...",
      "created_at": "2026-03-26T09:30:15Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 24
  }
}
```

消费者只看到 `user` 和 `assistant` 两种角色，看不到工程面板内部的操作。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cursor | string? | null | 游标 |
| limit | int (1-100) | 50 | 每页条数 |
| order | string | asc | `asc` 或 `desc` |

**状态：** 🆕 需新增

---

## 发送消息

### POST /api/v1/service/conversations/{conversation_id}/messages

> 在对话中发送消息。任何状态下都可以发，closed 的对话发消息会自动 reopen。

```
POST /api/v1/service/conversations/conv-001/messages
```

```json
{
  "content": "固定金额，10元。所有支付成功的订单都发。每人每个活动限领一张。"
}
```

**响应（流式 SSE）：**

```
Content-Type: text/event-stream

event: text
data: {"content": "明白了。还有两个细节需要确认：\n1. 优惠券的有效期...\n2. 使用门槛..."}

event: done
data: {"message_id": "msg-005", "conversation_updated_at": "2026-03-26T09:45:00Z"}
```

**向已关闭的对话发消息（自动 reopen）：**

```
event: status_changed
data: {"status": "open", "previous_status": "closed"}

event: text
data: {"content": "好的，我来看看之前的上下文..."}

event: done
data: {"message_id": "msg-009", "conversation_updated_at": "2026-03-27T10:00:00Z"}
```

**对话被上升时：**

```
event: text
data: {"content": "这个问题涉及第三方支付渠道的限制，我需要请团队成员确认。已转交团队，会尽快回复您。"}

event: status_changed
data: {"status": "escalated", "previous_status": "open"}

event: done
data: {"message_id": "msg-005", "conversation_updated_at": "2026-03-25T14:10:00Z"}
```

**SSE 事件类型：**

| 事件 | 说明 |
|------|------|
| `text` | Agent 的文本回复 |
| `status_changed` | 状态变更，含 `status` 和 `previous_status` |
| `error` | 错误信息 |
| `done` | 本轮响应结束 |

**状态：** 🆕 需新增

---

## 更新标签

### PUT /api/v1/service/conversations/{conversation_id}/labels

> 更新对话的标签。消费者和 workspace 成员都可以操作。

```
PUT /api/v1/service/conversations/conv-001/labels
```

```json
{
  "labels": ["feature-request", "payment"]
}
```

**响应：**

```json
{
  "id": "conv-001",
  "labels": ["feature-request", "payment"]
}
```

**状态：** 🆕 需新增

---

## 关闭对话

### POST /api/v1/service/conversations/{conversation_id}/close

> 关闭对话。消费者可以主动关闭自己的对话。

```
POST /api/v1/service/conversations/conv-001/close
```

**响应：**

```json
{
  "id": "conv-001",
  "status": "closed",
  "closed_at": "2026-03-26T15:00:00Z"
}
```

**状态：** 🆕 需新增

---

## 状态模型

### Conversation Status

```
open ←──────→ escalated
  │                │
  ↓                ↓
closed ←───── closed
  │
  ↓ (发新消息自动 reopen)
open
```

| 状态 | 说明 |
|------|------|
| `open` | 进行中，Agent 正在处理 |
| `escalated` | 已上升，等待 workspace 成员介入。消费者仍可发消息 |
| `closed` | 已关闭。消费者再发消息会自动 reopen 为 `open` |

**状态转换：**

| 从 | 到 | 触发方 | 说明 |
|----|----|--------|------|
| `open` | `escalated` | Agent 自动 / workspace 手动 | 需要人工介入 |
| `open` | `closed` | 消费者 / workspace | 问题解决或消费者主动关闭 |
| `escalated` | `open` | workspace | 介入后降级回正常处理 |
| `escalated` | `closed` | workspace | 问题解决 |
| `closed` | `open` | 消费者（发新消息自动触发） | 重新打开 |

---

## workspace 侧

每个 conversation 在 workspace 的 service inbox 中可见。Workspace 成员可以：

- 查看对话内容和状态
- 上升（escalate）或关闭（close）对话
- 在任意 session 中 @引用（如 `@conv-001`），作为工作上下文

详见 [workspace/conversations.md](../workspace/conversations.md)

---

## 响应模型

### Conversation

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 对话 ID |
| title | string | 对话标题（自动从第一条消息生成）|
| status | string | `open`、`escalated`、`closed` |
| labels | string[] | 标签列表 |
| closed_at | datetime? | 关闭时间，未关闭为 null |
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
| next_cursor | string? | 下一页游标 |
| has_more | bool | 是否有下一页 |
| total | int | 总数 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 参数校验失败 |
| 404 | 对话不存在 |
| 503 | 服务未激活 |

---

## 前端调用流程

```
消费者打开服务面板
  → GET /api/v1/service/info
  → GET /api/v1/service/conversations            # 默认显示 open + escalated

发起新对话
  → POST /api/v1/service/conversations            # 可带 labels

打开历史对话
  → GET /api/v1/service/conversations/{id}

继续对话（closed 的会自动 reopen）
  → POST /api/v1/service/conversations/{id}/messages

更新标签
  → PUT /api/v1/service/conversations/{id}/labels

关闭对话
  → POST /api/v1/service/conversations/{id}/close
```
