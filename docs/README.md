# teamagent.services

> 一个配置驱动的 AI Agent 服务框架。每个 agent-service 实例对外提供服务面板（消费者入口），对内提供工程面板（团队协作入口）。

---

## 双面板模型

```
                    agent-service 实例
                    ┌─────────────────────────────────┐
                    │                                 │
  外部消费者 ──────→ │  服务面板 (Service)              │
  （陈霜、张伟...）   │  /api/v1/service/*              │
                    │  • 发起工单 (conversation)        │
                    │  • 与 Agent 对话                  │
                    │                                 │
                    ├─────────────────────────────────┤
                    │                                 │
  团队成员 ────────→ │  工程面板 (Workspace)             │
  （赵琳、小李...）   │  /api/v1/workspace/*            │
                    │  • 在目录中开会话 (session)        │
                    │  • 浏览文件、执行命令              │
                    │  • 管理服务工单                   │
                    │                                 │
                    └─────────────────────────────────┘
```

- **服务面板** — 任何注册用户都可使用，面向外部消费者。对话以工单（conversation）形式管理，消费者看不到内部目录结构。
- **工程面板** — 需要被配置为 workspace member 才能进入，面向团队内部。在目录层级中创建会话（session），操作文件和终端。

---

## 核心概念

```
User（用户）
 └── 注册登录后获得身份
      ├── 任何 user → 可访问服务面板
      └── 被配置为 member → 可进入工程面板

Workspace（工作空间）
 └── 一个 agent-service 实例，由 .teamagent/teamagent.json 配置
      ├── providers — 大模型供应商，按 apiFormat 分类
      ├── harnesses — 执行引擎，声明支持的 apiFormats
      └── members — 团队成员（真人 + 外部服务）

Session（会话）— 工程面板
 └── 绑定到具体目录，存储在 {path}/.teamagent/sessions/
      ├── 选择 harness + provider/model
      ├── 对话、文件操作、终端命令
      └── 可 @member 或 @conversation

Conversation（工单）— 服务面板
 └── 面向外部消费者，存储在 .teamagent/conversations/
      ├── 消费者与 Agent 对话
      ├── 可被 escalate 到团队处理
      └── 工程面板中可查看和 @引用
```

---

## 供应商与引擎适配

Provider 声明 `apiFormat`，Harness 声明支持的 `apiFormats`，运行时按格式匹配：

```
providers                              harnesses
┌──────────────────────┐              ┌────────────────────────────┐
│ minmax               │              │ claude-agent-sdk           │
│   apiFormat: openai   │──────────┐  │   apiFormats: [anthropic]  │
│                      │          │  └────────────────────────────┘
│ claude               │          │
│   apiFormat: anthropic│─────┬───┼──┐
│                      │     │   │  │ ┌────────────────────────────┐
│ openai               │     │   └──┼─│ opencode                   │
│   apiFormat: openai   │─────┼──────┼─│   apiFormats: [openai,     │
└──────────────────────┘     │      │ │     anthropic, ollama]     │
                             │      │ └────────────────────────────┘
                             │      │
                             └──────┘
```

创建 session 时指定 harness 和 provider/model，系统校验 apiFormat 是否匹配。

---

## 跨服务协作

Member 中的 `service` 类型代表其他 agent-service 实例。在会话中 @ service member 时，系统通过对方的服务面板 API 发起请求，结果回流到当前会话：

```
产品团队 agent-service
├── session: "实现优惠券功能"
│   └── 消息: "@支付网关 支付成功后怎么触发发券？"
│                │
│                ↓ POST /api/v1/service/conversations
│
└── member: 支付网关 (type: service)
         serviceUrl: https://payment.agent.team.dev
                │
                ↓
    支付网关 agent-service（服务面板）
    └── 自动创建 conversation，Agent 回复
         └── 结果回流到产品团队的 session
```

---

## 数据存储

所有运行时数据存储在文件系统的 `.teamagent/` 目录下，无需数据库：

| 数据 | 位置 | 作用域 |
|------|------|--------|
| 配置 | `.teamagent/teamagent.json` | 仅启动目录 |
| 用户 | `.teamagent/users/` | 仅启动目录 |
| 工单 | `.teamagent/conversations/` | 仅启动目录 |
| 会话 | `.teamagent/sessions/` | 每个目录独立 |

详见 [数据存储文档](context/README.md)。

---

## 文档导航

### 配置（配置驱动，增删改通过配置文件）

| 文档 | 说明 |
|------|------|
| [config/README.md](config/README.md) | 配置驱动设计概览 |
| [config/providers.md](config/providers.md) | 供应商配置 |
| [config/harness.md](config/harness.md) | 引擎配置 |
| [config/members.md](config/members.md) | 成员配置 |

### API（只读查询 + 运行时操作）

| 文档 | 说明 |
|------|------|
| [api/user.md](api/user.md) | 用户注册、登录、个人信息 |
| [api/service/info.md](api/service/info.md) | 服务面板信息 |
| [api/service/conversations.md](api/service/conversations.md) | 服务面板工单（消费者视角） |
| [api/workspace/providers.md](api/workspace/providers.md) | 供应商查询和连通性测试 |
| [api/workspace/harness.md](api/workspace/harness.md) | 引擎查询 |
| [api/workspace/members.md](api/workspace/members.md) | 成员查询和连通性测试 |
| [api/workspace/sessions.md](api/workspace/sessions.md) | 会话管理和对话 |
| [api/workspace/sessions-files.md](api/workspace/sessions-files.md) | 会话内文件操作 |
| [api/workspace/sessions-terminal.md](api/workspace/sessions-terminal.md) | 会话内终端 |
| [api/workspace/conversations.md](api/workspace/conversations.md) | 工单管理（工程面板视角） |
| [api/workspace/stats.md](api/workspace/stats.md) | 目录统计 |

### 数据存储

| 文档 | 说明 |
|------|------|
| [context/README.md](context/README.md) | 存储结构概览 |
| [context/users.md](context/users.md) | 用户文件格式和认证流程 |
| [context/sessions.md](context/sessions.md) | 会话文件格式 |
| [context/conversations.md](context/conversations.md) | 工单文件格式 |
