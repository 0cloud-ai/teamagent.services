# .teamagent 数据存储

## 概述

teamagent.services 通过 `.teamagent/` 子目录存储运行时数据。数据分为两类：

- **启动目录专属** — 仅在启动目录的 `.teamagent/` 下存在，如配置、用户、服务工单
- **目录级上下文** — 每个工作目录都可以有自己的 `.teamagent/`，如会话记录

```
project/                              # 启动目录
├── .teamagent/
│   ├── teamagent.json                # 全局配置
│   ├── users/                        # 用户信息和登录凭据
│   ├── conversations/                # 服务工单（面向外部消费者）
│   └── sessions/                     # 当前目录层级的会话
│
├── src/
│   └── .teamagent/
│       └── sessions/                 # src/ 层级的会话
│
└── docs/
    └── .teamagent/
        └── sessions/                 # docs/ 层级的会话
```

## 设计原则

- 数据直接存储在文件系统，API 从文件系统读写，无需数据库
- 每个目录可以拥有自己的 `.teamagent/`，记录与该层级相关的上下文
- 未来可能扩展更多上下文内容（如目录级别的规则、缓存等）

## 启动目录专属

仅在启动目录的 `.teamagent/` 下存在，不随目录层级分布：

| 路径 | 文档 | 说明 |
|------|------|------|
| `.teamagent/users/` | [users.md](users.md) | 用户信息和登录凭据 |
| `.teamagent/conversations/` | [conversations.md](conversations.md) | 服务工单，面向外部消费者，与目录无关 |

## 目录级上下文

每个工作目录都可以有自己的 `.teamagent/`：

| 路径 | 文档 | 说明 |
|------|------|------|
| `.teamagent/sessions/` | [sessions.md](sessions.md) | 会话记录 |
