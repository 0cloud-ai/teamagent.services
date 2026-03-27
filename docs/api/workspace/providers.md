# Workspace — Providers API

> 管理大模型供应商。供应商是独立于 harness 的资源池，不同的 harness 引擎可以选择同一个供应商。

---

## 概念

**Provider（供应商）** 是大模型的连接配置，独立于 harness 存在。

```
agent-service
├── providers (独立资源池)
│   ├── prov-001: anthropic / claude-sonnet-4
│   ├── prov-002: anthropic / claude-opus-4
│   ├── prov-003: openai / gpt-4o
│   ├── prov-004: deepseek / deepseek-coder
│   └── prov-005: ollama / qwen3:32b
│
├── harness: claude-agent-sdk
│   └── 使用 → prov-001 (default), prov-002 (reasoning)
├── harness: opencode
│   └── 使用 → prov-001 (default), prov-003 (reasoning), prov-004 (fast)
└── harness: openclaw
    └── 使用 → prov-003 (default)
```

- 供应商统一配置一次，多个 harness 共享
- 每个 harness 通过绑定关系选择使用哪些供应商，并指定角色（default / reasoning / fast / local）
- 同一个供应商可以被多个 harness 同时使用

---

## 列出所有供应商

### GET /api/v1/workspace/providers

> 列出所有已配置的供应商。

```
GET /api/v1/workspace/providers
```

```json
{
  "providers": [
    {
      "id": "prov-001",
      "vendor": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "api_base": "https://api.anthropic.com",
      "status": "healthy",
      "used_by": ["claude-agent-sdk", "opencode"],
      "created_at": "2026-03-20T10:00:00Z"
    },
    {
      "id": "prov-002",
      "vendor": "anthropic",
      "model": "claude-opus-4-20250514",
      "api_base": "https://api.anthropic.com",
      "status": "healthy",
      "used_by": ["claude-agent-sdk"],
      "created_at": "2026-03-20T10:00:00Z"
    },
    {
      "id": "prov-003",
      "vendor": "openai",
      "model": "gpt-4o",
      "api_base": "https://api.openai.com",
      "status": "healthy",
      "used_by": ["opencode", "openclaw"],
      "created_at": "2026-03-22T14:00:00Z"
    },
    {
      "id": "prov-004",
      "vendor": "deepseek",
      "model": "deepseek-coder",
      "api_base": "https://api.deepseek.com",
      "status": "healthy",
      "used_by": ["opencode"],
      "created_at": "2026-03-22T14:00:00Z"
    },
    {
      "id": "prov-005",
      "vendor": "ollama",
      "model": "qwen3:32b",
      "api_base": "http://localhost:11434",
      "status": "healthy",
      "used_by": [],
      "created_at": "2026-03-25T09:00:00Z"
    }
  ]
}
```

**状态：** 🆕 需新增

---

## 添加供应商

### POST /api/v1/workspace/providers

> 添加一个大模型供应商到资源池。

```
POST /api/v1/workspace/providers
```

```json
{
  "vendor": "ollama",
  "model": "qwen3:32b",
  "api_base": "http://localhost:11434",
  "api_key": null
}
```

**响应：**

```json
{
  "id": "prov-005",
  "vendor": "ollama",
  "model": "qwen3:32b",
  "api_base": "http://localhost:11434",
  "status": "healthy",
  "used_by": [],
  "created_at": "2026-03-25T09:00:00Z"
}
```

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| vendor | string | 是 | 供应商标识：`anthropic`、`openai`、`deepseek`、`google`、`ollama`、`custom` |
| model | string | 是 | 模型名称 |
| api_base | string | 否 | API 地址，不传则使用供应商默认地址 |
| api_key | string | 否 | API 密钥，`ollama` 等本地供应商可为 null |

**状态：** 🆕 需新增

---

## 更新供应商

### PUT /api/v1/workspace/providers/{provider_id}

> 更新供应商配置。

```
PUT /api/v1/workspace/providers/prov-004
```

```json
{
  "model": "deepseek-coder-v2",
  "api_key": "sk-new-key..."
}
```

**响应：** 返回更新后的完整供应商对象。

**状态：** 🆕 需新增

---

## 删除供应商

### DELETE /api/v1/workspace/providers/{provider_id}

> 从资源池移除供应商。如果该供应商正被 harness 使用，需要先解绑。

```
DELETE /api/v1/workspace/providers/prov-005
```

**响应：**

```json
{
  "message": "已移除供应商 ollama/qwen3:32b"
}
```

**状态：** 🆕 需新增

---

## 测试连通性

### POST /api/v1/workspace/providers/{provider_id}/ping

> 测试供应商是否可用。

```
POST /api/v1/workspace/providers/prov-001/ping
```

**成功：**

```json
{
  "status": "healthy",
  "latency_ms": 234,
  "model": "claude-sonnet-4-20250514",
  "message": "连通正常"
}
```

**失败：**

```json
{
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
| id | string | 供应商配置 ID |
| vendor | string | 供应商标识 |
| model | string | 模型名称 |
| api_base | string | API 地址 |
| status | string | `healthy`、`unhealthy`、`unknown` |
| used_by | string[] | 正在使用该供应商的 harness 引擎 ID 列表 |
| created_at | datetime | 创建时间 |

### 支持的 vendor

| vendor | 默认 api_base | 说明 |
|--------|---------------|------|
| `anthropic` | `https://api.anthropic.com` | Claude 系列 |
| `openai` | `https://api.openai.com` | GPT 系列 |
| `deepseek` | `https://api.deepseek.com` | DeepSeek 系列 |
| `google` | `https://generativelanguage.googleapis.com` | Gemini 系列 |
| `ollama` | `http://localhost:11434` | 本地模型 |
| `custom` | （必须指定） | 自定义 OpenAI 兼容接口 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 参数校验失败 |
| 403 | 无权限（仅成员可操作）|
| 404 | 供应商不存在 |
| 409 | 删除时供应商仍被 harness 使用，需先解绑 |
