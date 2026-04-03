# 目录上下文 — Users（用户）

> 启动目录下的 `.teamagent/users/` 存储所有用户信息和登录凭据。用户数据直接存储在文件系统，API 从文件系统读写，无需数据库。

---

## 目录结构

```
<启动目录>/
└── .teamagent/
    └── users/
        ├── user-001.json
        ├── user-002.json
        └── user-003.json
```

每个用户一个 JSON 文件，以用户 ID 命名。

---

## user-{id}.json

```json
{
  "id": "user-002",
  "email": "chenshuang@company.com",
  "name": "陈霜",
  "salt": "a1b2c3d4e5f6...",
  "password_hash": "sha256:e3b0c44298fc1c14...",
  "created_at": "2026-02-01T09:00:00Z",
  "updated_at": "2026-02-01T09:00:00Z"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| email | string | 邮箱，全局唯一 |
| name | string | 显示名称 |
| salt | string | 随机盐值，注册时生成 |
| password_hash | string | 密码经 salt 加密后的哈希值 |
| created_at | datetime | 注册时间 |
| updated_at | datetime | 最后更新时间 |

---

## 认证流程

### 注册

1. 生成随机 `salt`
2. 用 `salt` + 明文密码计算 `password_hash`
3. 创建 `.teamagent/users/user-{id}.json`

### 登录验证

1. 按 email 扫描 `.teamagent/users/*.json` 找到用户文件
2. 读取文件中的 `salt`
3. 用 `salt` + 提交的密码计算哈希，与 `password_hash` 比对
4. 匹配则签发 token

### 修改密码

1. 验证旧密码（同登录流程）
2. 生成新 `salt`
3. 用新 `salt` + 新密码计算新 `password_hash`
4. 更新用户文件

---

## 安全说明

- 明文密码不存储，仅保存 salt 和哈希后的值
- 每个用户独立的 salt，防止彩虹表攻击
- `.teamagent/users/` 目录应设置合适的文件系统权限，限制非服务进程访问
