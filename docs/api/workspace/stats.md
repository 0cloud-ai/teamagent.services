# Workspace — Stats API

> 目录树的结构和统计信息。工程面板左侧 Explorer 的数据源。

---

## GET /api/v1/workspace/stats

> 获取根目录的统计信息和第一层子目录。

```
GET /api/v1/workspace/stats
```

```json
{
  "path": "/",
  "direct": { "directories": 1, "sessions": 0, "messages": 0 },
  "total": { "directories": 6, "sessions": 47, "messages": 1694 },
  "children": [
    { "name": "home", "total": { "directories": 5, "sessions": 42, "messages": 1534 } },
    { "name": "deploy", "total": { "directories": 0, "sessions": 5, "messages": 160 } }
  ]
}
```

**状态：** ✅ 已实现（需迁移路径前缀）

---

## GET /api/v1/workspace/stats/{path}

> 获取指定目录的统计信息和子目录。用于展开目录树节点时懒加载。

```
GET /api/v1/workspace/stats/home/linyuanzhou
```

```json
{
  "path": "/home/linyuanzhou",
  "direct": { "directories": 3, "sessions": 0, "messages": 0 },
  "total": { "directories": 3, "sessions": 24, "messages": 847 },
  "children": [
    { "name": "payment-gateway", "total": { "directories": 0, "sessions": 12, "messages": 423 } },
    { "name": "user-center", "total": { "directories": 0, "sessions": 8, "messages": 289 } },
    { "name": "notification-service", "total": { "directories": 0, "sessions": 4, "messages": 135 } }
  ]
}
```

**状态：** ✅ 已实现（需迁移路径前缀）

---

## 响应模型

### StatsResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| path | string | 当前目录路径 |
| direct | Counts | 本级直属统计（不含子目录）|
| total | Counts | 递归统计（含所有子目录）|
| children | ChildStats[] | 子目录列表及其统计 |

### Counts

| 字段 | 类型 | 说明 |
|------|------|------|
| directories | int | 子目录数 |
| sessions | int | 会话数 |
| messages | int | 消息数 |

### ChildStats

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 子目录名称 |
| total | Counts | 该子目录的递归统计 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 404 | 路径不存在 |

---

## 前端调用流程

```
页面加载
  → GET /api/v1/workspace/stats                    # 渲染第一层

展开 "home"
  → GET /api/v1/workspace/stats/home               # 懒加载子目录

展开 "linyuanzhou"
  → GET /api/v1/workspace/stats/home/linyuanzhou   # 懒加载子目录
```

每次只加载一层子目录，不递归获取整棵树。
