# Workspace — Providers API

> 查询和测试大模型供应商。供应商通过配置文件管理（见 [配置文档](../../config/providers.md)），API 仅提供查询和连通性测试。

---

## 概念

**Provider（供应商）** 是大模型的连接配置，独立于 harness 存在。

```
agent-service
├── providers (配置文件声明，每个供应商下挂多个模型)
│   ├── minmax
│   │   ├── kimi-k2-thinking
│   │   └── kimi-k2
│   ├── claude
│   │   ├── claude-sonnet-4
│   │   └── claude-opus-4
│   └── openai
│       ├── gpt-4o
│       └── o3
│
├── harness: opencode
│   └── 使用 → claude/claude-sonnet-4 (default), claude/claude-opus-4 (reasoning)
└── harness: openclaw
    └── 使用 → openai/gpt-4o (default)
```

- 供应商在 `.teamagent/teamagent.json` 中统一配置，多个 harness 共享
- 每个 harness 通过绑定关系选择使用哪些供应商，并指定角色（default / reasoning / fast / local）
- 同一个供应商可以被多个 harness 同时使用
- 供应商的增删改通过配置文件完成，API 仅提供只读查询和连通性测试

---

## 列出所有供应商

### GET /api/v1/workspace/providers

> 列出所有已配置的供应商。

```
GET /api/v1/workspace/providers
```

```json
{
  "providers": {
    "minmax": {
      "baseUrl": "https://api.minimax.chat",
      "apiFormat": "openai-completions",
      "status": "healthy",
      "models": [
        { "id": "kimi-k2-thinking", "name": "Kimi K2 Thinking", "status": "healthy" },
        { "id": "kimi-k2", "name": "Kimi K2", "status": "healthy" }
      ]
    },
    "claude": {
      "baseUrl": "https://api.anthropic.com",
      "apiFormat": "anthropic",
      "status": "healthy",
      "models": [
        { "id": "claude-sonnet-4", "name": "Claude Sonnet 4", "status": "healthy" },
        { "id": "claude-opus-4", "name": "Claude Opus 4", "status": "healthy" }
      ]
    },
    "openai": {
      "baseUrl": "https://api.openai.com",
      "apiFormat": "openai-completions",
      "status": "healthy",
      "models": [
        { "id": "gpt-4o", "name": "GPT-4o", "status": "healthy" },
        { "id": "o3", "name": "o3", "status": "healthy" }
      ]
    }
  }
}
```

**状态：** 🆕 需新增

---

## 测试连通性

### POST /api/v1/workspace/providers/{provider_name}/ping

> 测试供应商是否可用。可选指定模型 ID，不指定则测试供应商连通性。

```
POST /api/v1/workspace/providers/claude/ping
```

```json
{
  "model": "claude-sonnet-4"
}
```

**成功：**

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4",
  "status": "healthy",
  "latency_ms": 234,
  "message": "连通正常"
}
```

**失败：**

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4",
  "status": "unhealthy",
  "error": "401 Unauthorized: Invalid API key",
  "message": "认证失败，请检查 API 密钥"
}
```

**状态：** 🆕 需新增

---

## 响应模型

### Provider

| 字段 | 类型 | 说明 |
|------|------|------|
| baseUrl | string | API 地址 |
| apiFormat | string | API 协议格式 |
| status | string | `healthy`、`unhealthy`、`unknown` |
| models | Model[] | 该供应商下的模型列表 |

### Model

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 模型 ID |
| name | string | 模型显示名称 |
| status | string | `healthy`、`unhealthy`、`unknown` |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 403 | 无权限 |
| 404 | 供应商不存在 |
