# 配置 — Providers（供应商）

> 在 `.teamagent/teamagent.json` 的 `providers` 字段中配置大模型供应商。每个供应商下可挂载多个模型，harness 通过 `apiFormat` 适配供应商。

---

## 配置示例

```json
{
  "providers": {
    "minmax": {
      "baseUrl": "${MINMAX_ENDPOINT}",
      "apiKey": "${MINMAX_KEY}",
      "apiFormat": "openai-completions",
      "models": [
        { "id": "kimi-k2-thinking", "name": "Kimi K2 Thinking" },
        { "id": "kimi-k2", "name": "Kimi K2" }
      ]
    },
    "claude": {
      "baseUrl": "${CLAUDE_ENDPOINT}",
      "apiKey": "${CLAUDE_KEY}",
      "apiFormat": "anthropic",
      "models": [
        { "id": "claude-sonnet-4", "name": "Claude Sonnet 4" },
        { "id": "claude-opus-4", "name": "Claude Opus 4" }
      ]
    },
    "openai": {
      "baseUrl": "${OPENAI_ENDPOINT}",
      "apiKey": "${OPENAI_KEY}",
      "apiFormat": "openai-completions",
      "models": [
        { "id": "gpt-4o", "name": "GPT-4o" },
        { "id": "o3", "name": "o3" }
      ]
    }
  }
}
```

---

## 字段说明

### Provider（供应商）

`providers` 是一个对象，key 为供应商标识名（如 `minmax`、`claude`、`openai`），value 为供应商配置：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| baseUrl | string | 是 | API 地址，支持 `${ENV_VAR}` 环境变量插值 |
| apiKey | string | 否 | API 密钥，支持 `${ENV_VAR}` 环境变量插值。本地供应商可省略 |
| apiFormat | string | 是 | API 协议格式，见下方支持列表 |
| models | Model[] | 是 | 该供应商下可用的模型列表 |

### Model（模型）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 模型 ID，调用 API 时使用的标识 |
| name | string | 是 | 模型显示名称 |

---

## 环境变量插值

字符串值中的 `${VAR_NAME}` 会在服务启动时替换为对应的环境变量值。适用于 `baseUrl` 和 `apiKey` 字段，避免在配置文件中明文存储敏感信息。

```json
{
  "baseUrl": "${LLM_ENDPOINT}",
  "apiKey": "${LLM_KEY}"
}
```

---

## 支持的 API 协议格式

| apiFormat | 说明 |
|-----|------|
| `openai-completions` | OpenAI Chat Completions 兼容接口 |
| `anthropic` | Anthropic Messages API |
| `ollama` | Ollama 本地模型接口 |

---

## 与 harness 的适配关系

harness 不直接绑定具体的 provider，而是声明支持的 `apiFormats`。系统根据 provider 的 `apiFormat` 与 harness 的 `apiFormats` 匹配，确定哪些 provider/model 可被该 harness 使用。

```
provider: claude  (apiFormat: anthropic)           → harness: claude-agent-sdk (apiFormats: [anthropic]) ✓
provider: minmax  (apiFormat: openai-completions)  → harness: claude-agent-sdk (apiFormats: [anthropic]) ✗
provider: minmax  (apiFormat: openai-completions)  → harness: opencode (apiFormats: [openai-completions, anthropic]) ✓
```

详见 [harness 配置文档](harness.md)。

---

## 变更方式

供应商的增删改通过修改 `.teamagent/teamagent.json` 配置文件完成，而非通过 API。

- **添加供应商：** 在 `providers` 对象中新增 key
- **添加模型：** 在对应供应商的 `models` 数组中新增条目
- **删除供应商：** 移除对应 key

修改后重启服务或触发配置热加载生效。
