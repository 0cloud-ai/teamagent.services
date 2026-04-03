# Workspace — Harness API

> 查询 harness 引擎。Harness 通过配置文件管理（见 [配置文档](../../config/harness.md)），API 仅提供只读查询。

---

## 概念

**Harness 引擎**是 agent-service 的"手和脚"。不同的 harness 提供不同的 Agent 能力：

| 引擎 | 说明 |
|------|------|
| `claude-agent-sdk` | Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行 |
| `claude-code-cli` | Claude Code CLI 模式，贴近本地开发体验 |
| `opencode` | 开源 code agent 引擎，支持多种大模型供应商 |
| `openclaw` | 开源多模态 agent 引擎 |

**Harness 与 Provider 的关系：**

- Provider（供应商）是独立的资源池，见 [providers.md](providers.md)
- Harness 声明自己支持的 `apiFormats`，不直接绑定具体 provider
- 运行时根据 provider 的 `apiFormat` 与 harness 的 `apiFormats` 匹配，确定可用的 provider/model

**Harness 与 Session 的关系：**

- 创建 session 时选择使用哪个 harness 和 provider/model
- 系统校验 provider 的 `apiFormat` 是否在 harness 的 `apiFormats` 中
- session 一旦开始，harness 不可切换

```
agent-service
├── providers (配置文件声明)
│   ├── minmax    (apiFormat: openai-completions)
│   │   ├── kimi-k2-thinking
│   │   └── kimi-k2
│   ├── claude    (apiFormat: anthropic)
│   │   ├── claude-sonnet-4
│   │   └── claude-opus-4
│   └── openai    (apiFormat: openai-completions)
│       ├── gpt-4o
│       └── o3
│
├── harness: claude-agent-sdk (default)
│   └── apiFormats: [anthropic]
│       → 可用: claude/claude-sonnet-4, claude/claude-opus-4
├── harness: opencode
│   └── apiFormats: [openai-completions, anthropic, ollama]
│       → 可用: 所有 provider
│
├── session-A → harness: claude-agent-sdk + claude/claude-sonnet-4 (锁定)
└── session-B → harness: opencode + minmax/kimi-k2 (锁定)
```

> **TODO：** Harness 插件机制（安装/卸载/版本管理/第三方引擎注册）需要单独设计，当前文档只覆盖已有引擎的配置和使用。

---

## 列出所有引擎

### GET /api/v1/workspace/harness

> 列出所有已配置的 harness 引擎及其支持的 API 格式。

```
GET /api/v1/workspace/harness
```

```json
{
  "default": "claude-agent-sdk",
  "engines": {
    "claude-agent-sdk": {
      "engine": "claude-agent-sdk",
      "name": "Claude Agent SDK",
      "description": "Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行",
      "apiFormats": ["anthropic"]
    },
    "opencode": {
      "engine": "opencode",
      "name": "OpenCode",
      "description": "开源 code agent 引擎，支持多种大模型供应商",
      "apiFormats": ["openai-completions", "anthropic", "ollama"]
    },
    "openclaw": {
      "engine": "openclaw",
      "name": "OpenClaw",
      "description": "开源多模态 agent 引擎",
      "apiFormats": ["openai-completions"]
    }
  }
}
```

**状态：** 🆕 需新增

---

## 查看单个引擎详情

### GET /api/v1/workspace/harness/{harness_id}

> 获取指定引擎的详细信息。

```
GET /api/v1/workspace/harness/opencode
```

```json
{
  "engine": "opencode",
  "name": "OpenCode",
  "description": "开源 code agent 引擎，支持多种大模型供应商",
  "apiFormats": ["openai-completions", "anthropic", "ollama"]
}
```

**状态：** 🆕 需新增

---

## 响应模型

### Harness

| 字段 | 类型 | 说明 |
|------|------|------|
| engine | string | 引擎类型 |
| name | string | 引擎显示名 |
| description | string | 引擎描述 |
| apiFormats | string[] | 该引擎支持的 API 协议格式列表 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 403 | 无权限 |
| 404 | 引擎不存在 |
