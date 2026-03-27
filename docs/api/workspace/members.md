# Workspace — Members API

> 管理 agent-service 的成员。成员是统一的抽象，通过 `type` 区分真人和外部服务。

---

## 概念

**Member** 是 agent-service 工程面板中的参与者，统一用 `type` 区分：

| type | 说明 |
|------|------|
| `user` | 真人，通过工程面板登录进来干活 |
| `service` | 其他 agent-service 的服务面板，作为"虚拟同事"被拉进来 |

在会话中所有 member 都可以被 @，行为统一：
- `@赵琳` — 通知真人成员
- `@设计团队` — Agent 通过对方服务面板发起请求，结果回流到当前会话

```
产品团队 agent-service — members:
├── 赵琳     (type: user, role: owner)
├── 陈霜     (type: user, role: member)
├── 小李     (type: user, role: member)
├── 设计团队  (type: service, service_url: https://design.agent.team.dev)
├── 前端团队  (type: service, service_url: https://frontend.agent.team.dev)
├── 支付网关  (type: service, service_url: https://payment.agent.team.dev)
└── 后端团队  (type: service, service_url: https://backend.agent.team.dev)
```

---

## 列出所有成员

### GET /api/v1/workspace/members

> 列出所有成员。可按 type 过滤。

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
      "email": "zhaolin@company.com",
      "joined_at": "2026-01-15T10:00:00Z"
    },
    {
      "id": "mem-002",
      "type": "user",
      "name": "陈霜",
      "role": "member",
      "email": "chenshuang@company.com",
      "joined_at": "2026-02-01T09:00:00Z"
    },
    {
      "id": "mem-003",
      "type": "service",
      "name": "设计团队",
      "service_url": "https://design.agent.team.dev",
      "status": "connected",
      "joined_at": "2026-03-20T14:00:00Z"
    },
    {
      "id": "mem-004",
      "type": "service",
      "name": "支付网关",
      "service_url": "https://payment.agent.team.dev",
      "status": "connected",
      "joined_at": "2026-03-20T14:00:00Z"
    }
  ]
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string? | null | 按类型过滤：`user` 或 `service`，不传则返回全部 |

**状态：** 🆕 需新增

---

## 添加成员

### POST /api/v1/workspace/members

> 添加一个成员。根据 `type` 传不同的字段。

**添加用户：**

```
POST /api/v1/workspace/members
```

```json
{
  "type": "user",
  "email": "xiaoli@company.com",
  "role": "member"
}
```

```json
{
  "id": "mem-005",
  "type": "user",
  "name": "小李",
  "email": "xiaoli@company.com",
  "role": "member",
  "joined_at": "2026-03-27T10:00:00Z"
}
```

**添加外部服务：**

```
POST /api/v1/workspace/members
```

```json
{
  "type": "service",
  "name": "后端团队",
  "service_url": "https://backend.agent.team.dev"
}
```

系统自动调用对方 `GET /api/v1/service/info` 验证连通性。

```json
{
  "id": "mem-006",
  "type": "service",
  "name": "后端团队",
  "service_url": "https://backend.agent.team.dev",
  "service_info": {
    "name": "后端团队",
    "description": "后端服务开发，支持接口开发和业务逻辑实现",
    "status": "active"
  },
  "status": "connected",
  "joined_at": "2026-03-27T10:00:00Z"
}
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | `user` 或 `service` |
| email | string | type=user 时必填 | 用户邮箱 |
| role | string | 否 | type=user 时有效，`owner` 或 `member`，默认 `member` |
| name | string | type=service 时必填 | 显示名称（用于 @ 提及）|
| service_url | string | type=service 时必填 | 对方 agent-service 的服务面板地址 |

**状态：** 🆕 需新增

---

## 更新成员

### PUT /api/v1/workspace/members/{member_id}

> 更新成员信息。用户可改 role，外部服务可改 name。

**更新用户角色：**

```
PUT /api/v1/workspace/members/mem-002
```

```json
{
  "role": "owner"
}
```

**更新外部服务名称：**

```
PUT /api/v1/workspace/members/mem-003
```

```json
{
  "name": "设计组"
}
```

**状态：** 🆕 需新增

---

## 移除成员

### DELETE /api/v1/workspace/members/{member_id}

> 移除成员。不可移除最后一个 owner。

```
DELETE /api/v1/workspace/members/mem-005
```

```json
{
  "message": "已移除成员 小李"
}
```

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
POST /api/v1/workspace/sessions/{session_id}/messages
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
| joined_at | datetime | 加入时间 |

**type=user 附加字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| email | string | 邮箱 |
| role | string | `owner` 或 `member` |

**type=service 附加字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| service_url | string | 对方服务面板地址 |
| service_info | object? | 对方的服务信息（name, description, status）|
| status | string | `connected` 或 `disconnected` |

### Role（type=user）

| role | 说明 |
|------|------|
| `owner` | 所有者，可管理成员、配置 harness/provider、修改服务面板信息 |
| `member` | 普通成员，可在工程面板中工作 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 参数校验失败 / type 与字段不匹配 |
| 403 | 无权限（成员管理仅 owner 可操作）|
| 404 | 成员不存在 |
| 409 | 用户已是成员 / 外部服务已添加 / 不可移除最后一个 owner |
| 422 | ping 仅支持 type=service |
| 502 | 添加外部服务时对方服务面板不可达 |
