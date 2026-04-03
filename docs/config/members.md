# 配置 — Members（成员）

> 在 `.teamagent/teamagent.json` 的 `members` 字段中配置 workspace 成员。成员是统一的抽象，通过 `type` 区分真人和外部服务。

---

## 配置示例

```json
{
  "members": [
    {
      "id": "mem-001",
      "type": "user",
      "name": "赵琳",
      "email": "zhaolin@company.com",
      "role": "owner"
    },
    {
      "id": "mem-002",
      "type": "user",
      "name": "陈霜",
      "email": "chenshuang@company.com",
      "role": "member"
    },
    {
      "id": "mem-003",
      "type": "service",
      "name": "设计团队",
      "serviceUrl": "https://design.agent.team.dev"
    },
    {
      "id": "mem-004",
      "type": "service",
      "name": "支付网关",
      "serviceUrl": "https://payment.agent.team.dev"
    }
  ]
}
```

---

## 字段说明

### 基础字段（所有 type）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 成员 ID，全局唯一 |
| type | string | 是 | `user` 或 `service` |
| name | string | 是 | 显示名称，用于 @ 提及 |

### type=user 附加字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 用户邮箱，关联 `.teamagent/users/` 中的用户 |
| role | string | 否 | `owner` 或 `member`，默认 `member` |

### type=service 附加字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| serviceUrl | string | 是 | 对方 agent-service 的服务面板地址 |

---

## 成员类型

| type | 说明 |
|------|------|
| `user` | 真人，通过工程面板登录进来干活。email 关联 `.teamagent/users/` 中的用户账号 |
| `service` | 其他 agent-service 的服务面板，作为"虚拟同事"被拉进来 |

### Role（type=user）

| role | 说明 |
|------|------|
| `owner` | 所有者，可管理配置 |
| `member` | 普通成员，可在工程面板中工作 |

---

## @ 提及

在会话中所有 member 都可以被 @，行为统一：
- `@赵琳` — 通知真人成员
- `@设计团队` — Agent 通过对方服务面板发起请求，结果回流到当前会话

---

## 变更方式

成员的增删改通过修改 `.teamagent/teamagent.json` 的 `members` 字段完成，而非通过 API。

- **添加成员：** 在 `members` 数组中新增条目
- **修改成员：** 编辑对应条目的字段（如 role、name）
- **移除成员：** 移除对应条目

修改后重启服务或触发配置热加载生效。
