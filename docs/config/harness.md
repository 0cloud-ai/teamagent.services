# 配置 — Harnesses（引擎）

> 在 `.teamagent/teamagent.json` 的 `harnesses` 字段中配置 harness 引擎。Harness 是 agent-service 的执行引擎，通过声明支持的 `apiFormat` 来适配供应商。

---

## 配置示例

```json
{
  "harnesses": {
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
}
```

---

## 字段说明

### Harness

`harnesses` 对象包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| default | string | 否 | 新建 session 时默认使用的引擎 key。不指定则使用 `engines` 中第一个 |
| engines | object | 是 | 引擎配置，key 为引擎标识名，value 为引擎配置 |

### Engine（引擎）

`engines` 中每个引擎的配置：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| engine | string | 是 | 引擎类型，见下方支持列表 |
| name | string | 否 | 引擎显示名称 |
| description | string | 否 | 引擎描述 |
| apiFormats | string[] | 是 | 该引擎支持的 API 协议格式列表 |

---

## 支持的引擎类型

| engine | 说明 |
|--------|------|
| `claude-agent-sdk` | Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行 |
| `claude-code-cli` | Claude Code CLI 模式，贴近本地开发体验 |
| `opencode` | 开源 code agent 引擎，支持多种大模型供应商 |
| `openclaw` | 开源多模态 agent 引擎 |

---

## Harness 与 Provider 的适配

Harness 不直接绑定具体的 provider 或 model，而是声明自己支持哪些 `apiFormat`。运行时系统根据 provider 的 `apiFormat` 与 harness 的 `apiFormats` 进行匹配，确定哪些 provider/model 可被该 harness 使用。

```
provider: minmax   (apiFormat: openai-completions)  ──┐
provider: openai   (apiFormat: openai-completions)  ──┼── harness: opencode (apiFormats: openai-completions, anthropic, ollama)
provider: claude   (apiFormat: anthropic)           ──┘

provider: claude   (apiFormat: anthropic)           ──── harness: claude-agent-sdk (apiFormats: anthropic)

provider: minmax   (apiFormat: openai-completions)  ──┐
provider: openai   (apiFormat: openai-completions)  ──┴── harness: openclaw (apiFormats: openai-completions)
```

- 一个 harness 可以适配多种 `apiFormat`，从而使用多个供应商
- 一个 provider 可以被多个 harness 使用，只要 `apiFormat` 匹配
- 具体使用哪个 provider/model 在创建 session 时指定

---

## 与 Session 的关系

- 创建 session 时选择使用哪个 harness（不指定则用 `harnesses.default`）
- 同时指定使用哪个 provider/model，系统校验该 provider 的 `apiFormat` 是否在 harness 的 `apiFormats` 中
- session 一旦开始，harness 不可切换

---

## 变更方式

harness 的增删改通过修改 `.teamagent/teamagent.json` 配置文件完成，而非通过 API。

- **添加引擎：** 在 `engines` 中新增 key
- **调整适配格式：** 编辑对应引擎的 `apiFormats`
- **删除引擎：** 移除对应 key
- **切换默认引擎：** 修改 `harnesses.default`

修改后重启服务或触发配置热加载生效。
