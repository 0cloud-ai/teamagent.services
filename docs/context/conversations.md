# Conversations（服务工单）

> 启动目录下的 `.teamagent/conversations/` 统一存储所有服务面板的工单。Conversations 面向外部消费者，与目录结构无关，不属于目录上下文。

---

## 目录结构

```
<启动目录>/
└── .teamagent/
    └── conversations/
        ├── conv-001/
        │   ├── conversation.json       # 工单元信息
        │   └── messages.jsonl          # 对话记录（追加写入）
        ├── conv-002/
        │   ├── conversation.json
        │   └── messages.jsonl
        └── conv-003/
            ├── conversation.json
            └── messages.jsonl
```

每个工单一个子目录，以 conversation ID 命名。

---

## conversation.json

存储工单的元信息，创建时写入，后续按需更新（状态变更、标签修改、message_count 递增）。

```json
{
  "id": "conv-001",
  "title": "支付成功后发放优惠券",
  "status": "open",
  "labels": ["feature-request"],
  "user_id": "user-002",
  "created_at": "2026-03-26T09:30:00Z",
  "updated_at": "2026-03-26T15:00:00Z",
  "closed_at": null,
  "message_count": 24
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 工单 ID |
| title | string | 工单标题（自动从第一条消息生成） |
| status | string | `open`、`escalated`、`closed` |
| labels | string[] | 标签列表 |
| user_id | string | 发起者的用户 ID |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |
| closed_at | datetime? | 关闭时间，未关闭为 null |
| message_count | int | 消息总数 |

---

## messages.jsonl

对话记录，每行一条 JSON，追加写入。消费者视角只有 `user` 和 `assistant` 两种角色。

```jsonl
{"id":"msg-001","role":"user","content":"支付成功后给用户发一张优惠券，想了解一下技术上怎么实现，需要多久。","created_at":"2026-03-26T09:30:00Z"}
{"id":"msg-002","role":"assistant","content":"好的，关于支付成功后发放优惠券，我需要确认几个细节：...","created_at":"2026-03-26T09:30:15Z"}
{"id":"msg-003","role":"user","content":"固定金额，10元。所有支付成功的订单都发。","created_at":"2026-03-26T09:45:00Z"}
```

### Message

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息 ID |
| role | string | `user` 或 `assistant` |
| content | string | 消息内容 |
| created_at | datetime | 发送时间 |

---

## 状态模型

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
| `escalated` | 已上升，等待 workspace 成员介入 |
| `closed` | 已关闭。消费者再发消息会自动 reopen |

状态变更时更新 `conversation.json` 中的 `status` 和相关时间字段。
