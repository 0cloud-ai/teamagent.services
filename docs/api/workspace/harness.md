# Workspace — Harness API

> 管理工程面板的 harness 引擎。Harness 是 agent-service 的执行引擎，决定了 Agent 用什么方式来读写文件、执行命令、与大模型交互。

---

## 概念

**Harness 引擎**是 agent-service 的"手和脚"。不同的 harness 提供不同的 Agent 能力：

| 引擎 | 说明 |
|------|------|
| `claude-agent-sdk` | Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行 |
| `claude-code-cli` | Claude Code CLI 模式，贴近本地开发体验 |
| `opencode` | 开源 code agent 引擎 |
| `openclaw` | 开源多模态 agent 引擎 |

**Harness 与 Provider 的关系：**

- Provider（供应商）是独立的资源池，见 [providers.md](providers.md)
- Harness 通过**绑定**来选择使用哪些供应商，并为每个绑定指定角色（default / reasoning / fast / local）
- 不同的 harness 可以绑定同一个供应商
- 一个 harness 可以绑定多个供应商，按角色区分用途

**Harness 与 Session 的关系：**

- 创建 session 时选择使用哪个 harness（不指定则用 default）
- **session 一旦开始，harness 不可切换**
- 可以设置一个 **default harness**，新建 session 时自动使用

```
agent-service
├── providers (独立资源池)
│   ├── prov-001: anthropic / claude-sonnet-4
│   ├── prov-002: anthropic / claude-opus-4
│   └── prov-003: openai / gpt-4o
│
├── harness: claude-agent-sdk (default)
│   ├── binding: prov-001 → role: default
│   └── binding: prov-002 → role: reasoning
├── harness: opencode
│   ├── binding: prov-001 → role: default    ← 和上面共享同一个供应商
│   └── binding: prov-003 → role: reasoning
│
├── session-A → harness: claude-agent-sdk (锁定)
└── session-B → harness: opencode (锁定)
```

> **TODO：** Harness 插件机制（安装/卸载/版本管理/第三方引擎注册）需要单独设计，当前文档只覆盖已有引擎的配置和使用。

---

## 列出所有引擎

### GET /api/v1/workspace/harness

> 列出所有已配置的 harness 引擎、绑定关系及 default 设置。

```
GET /api/v1/workspace/harness
```

```json
{
  "default": "claude-agent-sdk",
  "engines": [
    {
      "id": "claude-agent-sdk",
      "name": "Claude Agent SDK",
      "description": "Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行",
      "supported_vendors": ["anthropic"],
      "bindings": [
        { "provider_id": "prov-001", "vendor": "anthropic", "model": "claude-sonnet-4-20250514", "role": "default" },
        { "provider_id": "prov-002", "vendor": "anthropic", "model": "claude-opus-4-20250514", "role": "reasoning" }
      ]
    },
    {
      "id": "opencode",
      "name": "OpenCode",
      "description": "开源 code agent 引擎，支持多种大模型供应商",
      "supported_vendors": ["anthropic", "openai", "deepseek", "google", "ollama"],
      "bindings": [
        { "provider_id": "prov-001", "vendor": "anthropic", "model": "claude-sonnet-4-20250514", "role": "default" },
        { "provider_id": "prov-003", "vendor": "openai", "model": "gpt-4o", "role": "reasoning" }
      ]
    }
  ]
}
```

**状态：** 🆕 需新增

---

## 设置默认引擎

### PUT /api/v1/workspace/harness/default

> 设置新建 session 时默认使用的 harness 引擎。

```
PUT /api/v1/workspace/harness/default
```

```json
{
  "engine_id": "opencode"
}
```

**响应：**

```json
{
  "default": "opencode",
  "message": "默认引擎已设置为 OpenCode"
}
```

仅影响后续新建的 session。已有 session 的 harness 不受影响。

**状态：** 🆕 需新增

---

## 查看单个引擎详情

### GET /api/v1/workspace/harness/engines/{engine_id}

> 获取指定引擎的详细信息和供应商绑定。

```
GET /api/v1/workspace/harness/engines/opencode
```

```json
{
  "id": "opencode",
  "name": "OpenCode",
  "description": "开源 code agent 引擎，支持多种大模型供应商",
  "supported_vendors": ["anthropic", "openai", "deepseek", "google", "ollama"],
  "bindings": [
    { "provider_id": "prov-001", "vendor": "anthropic", "model": "claude-sonnet-4-20250514", "role": "default" },
    { "provider_id": "prov-003", "vendor": "openai", "model": "gpt-4o", "role": "reasoning" }
  ]
}
```

**状态：** 🆕 需新增

---

## 绑定供应商到引擎

### POST /api/v1/workspace/harness/engines/{engine_id}/bindings

> 将一个已有的供应商绑定到指定引擎，并分配角色。

```
POST /api/v1/workspace/harness/engines/opencode/bindings
```

```json
{
  "provider_id": "prov-004",
  "role": "fast"
}
```

**响应：**

```json
{
  "provider_id": "prov-004",
  "vendor": "deepseek",
  "model": "deepseek-coder",
  "role": "fast"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| provider_id | string | 是 | 供应商 ID（必须已存在于资源池中）|
| role | string | 否 | 角色，默认 `default`。可选：`default`、`reasoning`、`fast`、`local` |

**状态：** 🆕 需新增

---

## 更新绑定角色

### PUT /api/v1/workspace/harness/engines/{engine_id}/bindings/{provider_id}

> 修改某个绑定的角色。

```
PUT /api/v1/workspace/harness/engines/opencode/bindings/prov-003
```

```json
{
  "role": "fast"
}
```

**状态：** 🆕 需新增

---

## 解绑供应商

### DELETE /api/v1/workspace/harness/engines/{engine_id}/bindings/{provider_id}

> 从引擎中移除一个供应商绑定。

```
DELETE /api/v1/workspace/harness/engines/opencode/bindings/prov-003
```

**响应：**

```json
{
  "message": "已从 OpenCode 解绑供应商 openai/gpt-4o"
}
```

**状态：** 🆕 需新增

---

## 响应模型

### Engine

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 引擎标识符 |
| name | string | 引擎显示名 |
| description | string | 引擎描述 |
| supported_vendors | string[] | 支持的供应商类型列表 |
| bindings | Binding[] | 已绑定的供应商及角色 |

### Binding

| 字段 | 类型 | 说明 |
|------|------|------|
| provider_id | string | 供应商 ID |
| vendor | string | 供应商类型（冗余，便于展示）|
| model | string | 模型名称（冗余，便于展示）|
| role | string | `default`、`reasoning`、`fast`、`local` |

### Binding role

| role | 说明 |
|------|------|
| `default` | 日常任务，引擎默认使用 |
| `reasoning` | 复杂推理任务 |
| `fast` | 快速响应，轻量模型 |
| `local` | 本地模型，无网络依赖 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | engine_id 不存在 / provider 的 vendor 不在引擎 supported_vendors 中 |
| 403 | 无权限（仅成员可操作）|
| 404 | 引擎或供应商不存在 |
| 409 | 解绑正在运行中 session 使用的唯一 default 供应商 |
