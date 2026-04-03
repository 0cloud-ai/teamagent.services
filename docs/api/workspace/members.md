# Workspace — Members API

> 查询和测试 workspace 成员。成员通过配置文件管理（见 [配置文档](../../config/members.md)），API 仅提供只读查询和连通性测试。

---

## 概念

**Member** 是 agent-service 工程面板中的参与者，在 `.teamagent/teamagent.json` 的 `members` 字段中配置，统一用 `type` 区分：

| type | 说明 |
|------|------|
| `user` | 真人，通过工程面板登录进来干活 |
| `service` | 其他 agent-service 的服务面板，作为"虚拟同事"被拉进来 |

在会话中所有 member 都可以被 @，行为统一：
- `@赵琳` — 通知真人成员
- `@设计团队` — Agent 通过对方服务面板发起请求，结果回流到当前会话

```
产品团队 agent-service — members (配置文件声明):
├── 赵琳     (type: user, role: owner)
├── 陈霜     (type: user, role: member)
├── 小李     (type: user, role: member)
├── 设计团队  (type: service, serviceUrl: https://design.agent.team.dev)
├── 前端团队  (type: service, serviceUrl: https://frontend.agent.team.dev)
├── 支付网关  (type: service, serviceUrl: https://payment.agent.team.dev)
└── 后端团队  (type: service, serviceUrl: https://backend.agent.team.dev)
```

- 成员的增删改通过配置文件完成，API 仅提供只读查询和连通性测试

---

## 列出所有成员

### GET /api/v1/workspace/members

> 读取配置文件中的成员列表。可按 type 过滤。

```
GET /api/v1/workspace/members
```

```json
{
  "members": [
    {
      "id": "mem-001",
      "type": "user",
      "name": "赵琳",
      "role": "owner",
      "email": "zhaolin@company.com"
    },
    {
      "id": "mem-002",
      "type": "user",
      "name": "陈霜",
      "role": "member",
      "email": "chenshuang@company.com"
    },
    {
      "id": "mem-003",
      "type": "service",
      "name": "设计团队",
      "serviceUrl": "https://design.agent.team.dev",
      "status": "connected"
    },
    {
      "id": "mem-004",
      "type": "service",
      "name": "支付网关",
      "serviceUrl": "https://payment.agent.team.dev",
      "status": "connected"
    }
  ]
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string? | null | 按类型过滤：`user` 或 `service`，不传则返回全部 |

**状态：** 🆕 需新增

---

## 测试连通性

### POST /api/v1/workspace/members/{member_id}/ping

> 测试外部服务成员的连通性。仅对 type=service 有效。

```
POST /api/v1/workspace/members/mem-003/ping
```

**成功：**

```json
{
  "status": "connected",
  "latency_ms": 120,
  "service_info": {
    "name": "设计团队",
    "description": "UI/UX 设计服务",
    "status": "active"
  }
}
```

**失败：**

```json
{
  "status": "disconnected",
  "error": "Connection refused",
  "message": "无法连接到 https://design.agent.team.dev"
}
```

**状态：** 🆕 需新增

---

## @ 提及机制

在会话中发消息时，可以通过 `mentions` 引用任意成员：

```
POST /api/v1/workspace/sessions/{session_id}/messages?path=...
```

```json
{
  "content": "这个需求涉及四个团队：\n1. @设计团队 — 活动页面\n2. @前端团队 — 页面开发\n3. @支付网关 — 优惠券\n4. @后端团队 — 折扣逻辑",
  "mentions": ["mem-003", "mem-005", "mem-004", "mem-006"]
}
```

- @ user 成员 → 发送通知
- @ service 成员 → Agent 通过对方服务面板发起请求，响应回流到当前会话

`mentions` 是 member_id 数组，不区分 type，系统根据成员类型自动处理。

---

## 响应模型

### Member

所有成员共享基础字段，type 不同时附加不同字段：

**基础字段（所有 type）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 成员 ID |
| type | string | `user` 或 `service` |
| name | string | 显示名称 |

**type=user 附加字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| email | string | 邮箱 |
| role | string | `owner` 或 `member` |

**type=service 附加字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| serviceUrl | string | 对方服务面板地址 |
| status | string | `connected` 或 `disconnected` |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 403 | 无权限 |
| 404 | 成员不存在 |
| 422 | ping 仅支持 type=service |
