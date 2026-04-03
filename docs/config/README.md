# 配置驱动设计

## 概述

teamagent.services 采用**配置驱动**架构。服务启动时从工作目录下的 `.teamagent/teamagent.json` 读取配置，将供应商、harness 引擎等资源的管理从 API 写入转移到配置文件中。

这意味着：

- **供应商、harness 等资源通过配置文件声明**，而非通过 API 创建
- **API 仅提供查询和运行时操作**（如列表查询、连通性测试），不负责资源的增删改
- **部署和变更通过修改配置文件 + 重启/热加载完成**，便于版本控制和审计

## 配置文件位置

```
<工作目录>/
└── .teamagent/
    └── teamagent.json        # 主配置文件
```

服务按以下顺序查找配置：

1. 启动命令指定的路径（`--config` 参数）
2. 当前工作目录下的 `.teamagent/teamagent.json`

## 配置结构概览

```json
{
  "providers": {
    "claude": {
      "baseUrl": "${CLAUDE_ENDPOINT}",
      "apiKey": "${CLAUDE_KEY}",
      "apiFormat": "anthropic",
      "models": [
        { "id": "claude-sonnet-4", "name": "Claude Sonnet 4" }
      ]
    }
  },
  "harnesses": {
    "default": "claude-agent-sdk",
    "engines": {
      "claude-agent-sdk": {
        "engine": "claude-agent-sdk",
        "apiFormats": ["anthropic"]
      }
    }
  },
  "members": [
    { "id": "mem-001", "type": "user", "name": "赵琳", "email": "zhaolin@company.com", "role": "owner" },
    { "id": "mem-003", "type": "service", "name": "设计团队", "serviceUrl": "https://design.agent.team.dev" }
  ]
}
```

> 字符串值中的 `${VAR_NAME}` 在启动时替换为对应环境变量。

## 配置项文档

| 配置项 | 文档 |
|--------|------|
| providers（供应商） | [providers.md](providers.md) |
| harnesses（引擎） | [harness.md](harness.md) |
| members（成员） | [members.md](members.md) |
