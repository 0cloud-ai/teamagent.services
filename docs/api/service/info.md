# Service — Info API

> 获取 agent-service 对外暴露的服务信息。服务面板首页的数据源。

---

## GET /api/v1/service/info

> 获取服务基本信息。外部消费者打开服务面板时首先调用此接口。

```
GET /api/v1/service/info
```

```json
{
  "name": "支付网关",
  "description": "由工程团队维护 · 支持支付流程相关咨询和需求",
  "status": "active",
  "capabilities": [
    "支付流程咨询",
    "需求评估与排期",
    "技术方案讨论",
    "功能开发与交付"
  ]
}
```

**响应模型：**

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 服务名称 |
| description | string | 服务描述 |
| status | string | `active` 或 `inactive` |
| capabilities | string[] | 服务能力列表 |

---

## PUT /api/v1/service/info

> 更新服务信息。仅工程面板成员可操作。

```
PUT /api/v1/service/info
```

```json
{
  "name": "支付网关",
  "description": "由工程团队维护 · 支持支付流程相关咨询和需求",
  "status": "active",
  "capabilities": [
    "支付流程咨询",
    "需求评估与排期",
    "技术方案讨论",
    "功能开发与交付"
  ]
}
```

**状态：** 🆕 需新增

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 403 | 无权限（PUT 仅限成员）|
| 503 | 服务未激活 |
