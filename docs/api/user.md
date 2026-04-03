# User API

> 用户账号管理：注册、登录、个人信息。User 是 agent-service 的最顶层身份，决定了你能访问什么。
>
> 用户数据存储在启动目录的 `.teamagent/users/` 下（见 [用户上下文](../context/users.md)），每个用户一个 JSON 文件，登录凭据通过 salt + hash 存储。

---

## 概念

**User** 是使用 agent-service 的人。每个 user 有两种访问路径：

- **服务面板** — 任何 user 都可以直接使用，无需额外权限。这是对外的门。
- **工程面板** — 需要被绑定为 workspace 的 member 才能进入。这是内部的门。

```
User: 陈霜
├── 可以访问：服务面板（任何 user 都行）
│   └── 通过 /api/v1/service/* 与 agent-service 对话
│
└── 如果被添加为 workspace member：
    └── 可以访问：工程面板
        └── 通过 /api/v1/workspace/* 操作目录、会话、文件等
```

一个 user 可以是多个 agent-service 的 member（比如同时在支付团队和基础设施团队的 agent-service 里工作）。

---

## 注册

### POST /api/v1/user/register

> 注册新用户。在 `.teamagent/users/` 下创建用户文件，生成 salt 并存储密码哈希。

```
POST /api/v1/user/register
```

```json
{
  "email": "chenshuang@company.com",
  "password": "********",
  "name": "陈霜"
}
```

**响应：**

```json
{
  "id": "user-002",
  "email": "chenshuang@company.com",
  "name": "陈霜",
  "created_at": "2026-02-01T09:00:00Z",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱，作为唯一标识 |
| password | string | 是 | 密码 |
| name | string | 是 | 显示名称 |

实现：
1. 扫描 `.teamagent/users/*.json` 检查 email 唯一性
2. 生成随机 salt，计算 password_hash
3. 写入 `.teamagent/users/user-{id}.json`
4. 签发 token 返回

**状态：** 🆕 需新增

---

## 登录

### POST /api/v1/user/login

> 用户登录，读取用户文件验证密码，返回 token。

```
POST /api/v1/user/login
```

```json
{
  "email": "chenshuang@company.com",
  "password": "********"
}
```

**响应：**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "user-002",
    "email": "chenshuang@company.com",
    "name": "陈霜"
  }
}
```

后续请求通过 `Authorization: Bearer <token>` 携带身份。

实现：
1. 按 email 扫描 `.teamagent/users/*.json` 找到用户文件
2. 读取 salt，用 salt + 提交密码计算哈希，与 password_hash 比对
3. 匹配则签发 token

**状态：** 🆕 需新增

---

## 退出

### POST /api/v1/user/logout

> 注销当前 token。

```
POST /api/v1/user/logout
```

**响应：**

```json
{
  "message": "已退出登录"
}
```

**状态：** 🆕 需新增

---

## 获取当前用户信息

### GET /api/v1/user/me

> 读取当前登录用户的文件，返回用户信息及所关联的 workspace memberships。

```
GET /api/v1/user/me
```

```json
{
  "id": "user-002",
  "email": "chenshuang@company.com",
  "name": "陈霜",
  "created_at": "2026-02-01T09:00:00Z",
  "memberships": [
    {
      "member_id": "mem-002",
      "workspace_name": "支付网关",
      "workspace_url": "https://payment.agent.team.dev",
      "role": "member"
    },
    {
      "member_id": "mem-010",
      "workspace_name": "产品团队",
      "workspace_url": "https://product.agent.team.dev",
      "role": "owner"
    }
  ]
}
```

`memberships` 列出该用户作为 member 加入的所有 agent-service workspace，用户可以据此切换进入不同的工程面板。

**状态：** 🆕 需新增

---

## 更新用户信息

### PUT /api/v1/user/me

> 更新当前用户的个人信息，写回用户文件。

```
PUT /api/v1/user/me
```

```json
{
  "name": "陈霜（产品）"
}
```

**响应：** 返回更新后的完整用户对象（不含 memberships）。

**状态：** 🆕 需新增

---

## 修改密码

### PUT /api/v1/user/me/password

> 修改当前用户密码。验证旧密码后，生成新 salt 和 password_hash，更新用户文件。

```
PUT /api/v1/user/me/password
```

```json
{
  "old_password": "********",
  "new_password": "********"
}
```

**响应：**

```json
{
  "message": "密码已更新"
}
```

**状态：** 🆕 需新增

---

## 访问权限总结

| 接口前缀 | 条件 | 说明 |
|----------|------|------|
| `/api/v1/user/*` | 无需登录（register/login）或已登录 | 用户账号管理 |
| `/api/v1/service/*` | 已登录 | 任何 user 都可访问服务面板 |
| `/api/v1/workspace/*` | 已登录 + 是该 workspace 的 member | 需要被绑定为 member 才能进入工程面板 |

当 workspace owner 通过 `POST /api/v1/workspace/members` 添加一个 user 类型的 member 时，该 user 的 `GET /me` 响应里会自动出现对应的 membership，用户就可以进入该工程面板了。

---

## 响应模型

### User

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| email | string | 邮箱 |
| name | string | 显示名称 |
| created_at | datetime | 注册时间 |

### Membership

| 字段 | 类型 | 说明 |
|------|------|------|
| member_id | string | 在该 workspace 中的 member ID |
| workspace_name | string | workspace 名称 |
| workspace_url | string | workspace 地址 |
| role | string | `owner` 或 `member` |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 参数校验失败 |
| 401 | 未登录 / token 无效或过期 |
| 409 | 邮箱已注册 |
