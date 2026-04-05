# 前端重构设计文档

## 概述

将当前前端重构为基于 shadcn Sidebar + Application Shell 的四栏布局，使用 Zustand 进行状态管理。后端已运行在 3000 端口，本次只做纯前端工作。

## 布局结构

四栏布局，从左到右：

### 1. 左侧栏（参考 sidebar17.tsx）

- **SidebarHeader**
  - WorkspaceSwitcher：纯展示模式，显示服务名称和描述（从 serviceInfoApi 获取），保留 sidebar17 的下拉样式但不做切换功能
  - Tabs：三个图标 Tab — Files / Datas / Services
    - Files：当前实现，显示目录树
    - Datas：TODO 占位
    - Services：TODO 占位

- **SidebarContent**
  - Files Tab 内容：目录树导航
    - 数据源：statsApi.get(path) 返回的 children 字段
    - 点击目录 → 更新 workspaceStore.currentPath → 右侧 Session 列表刷新
    - 展示为 SidebarMenu + SidebarMenuButton 列表
    - 支持点击进入子目录，顶部有返回上级按钮

- **SidebarFooter**
  - NavUser 组件：用户头像、名称、邮箱、下拉菜单（退出登录）

- **SidebarRail**：可折叠轨道

### 2. Session 列表面板（参考 shell10 的 TicketListPanel）

- 位于 SidebarInset 内部左侧，固定宽度 `w-1/4 max-w-[320px] min-w-[240px]`
- Header：显示当前目录路径 + "+" 创建新 session 按钮
- 列表项：session title、最近消息预览、消息数、时间
- 数据源：sessionsApi.list(currentPath)
- 点击 session → 更新 sessionStore.selectedSessionId

### 3. 会话区（参考 shell10 的对话区）

- Header：session 标题 + 状态 + 切换右侧详情面板按钮（PanelRight 图标）
- 消息列表：ScrollArea 包裹
  - message 类型：显示 role（user/assistant）、content、时间
  - event 类型：显示 actor、action、target、detail（系统事件样式）
- 底部输入框：UI 占位，Textarea + Send 按钮，暂不实现发送功能
- 数据源：sessionsApi.getMessages(sessionId)

### 4. 详情面板（参考 shell10 的 InboxAgentPanel，群聊 settings 风格）

- 可通过 Header 按钮切换显示/隐藏
- 固定宽度 `w-1/4 max-w-[360px] min-w-[280px]`
- 内容：
  - Session 基本信息：harness、创建时间、更新时间、消息数
  - 成员列表：头像 + 名称 + 加入方式（creator/mention/manual）
  - "添加成员" 按钮：UI only，功能不实现
- 数据源：session 对象 + sessionsApi.listMembers(sessionId)

## 状态管理（Zustand）

### useAuthStore
- state: token, user, isLoading
- actions: login, register, logout, validateToken
- 从 localStorage 持久化 token

### useWorkspaceStore
- state: currentPath, directoryTree (children from stats), sessions[], isLoadingSessions
- actions: setPath, fetchStats, fetchSessions
- currentPath 变化时自动 fetchSessions

### useSessionStore
- state: selectedSessionId, messages[], members[], isLoadingMessages
- actions: selectSession, fetchMessages, fetchMembers
- selectedSessionId 变化时自动 fetch messages 和 members

### useUIStore
- state: activeTab ('files' | 'datas' | 'services'), isDetailPanelOpen
- actions: setActiveTab, toggleDetailPanel

## 技术选型

- UI 组件：shadcn/ui（已有的 sidebar, button, avatar, badge, scroll-area, tabs, dropdown-menu, separator, textarea, tooltip 等）
- 状态管理：Zustand（新增依赖）
- 样式：Tailwind CSS v4（已有）
- 图标：lucide-react（已有）
- 路由：保持 Next.js App Router（/, /login, /service）
- API 代理：Next.js rewrites 代理到 localhost:3000

## 文件结构

```
src/
├── app/
│   ├── layout.tsx              # 保持，移除 AuthProvider 改用 Zustand
│   ├── globals.css             # 保持
│   ├── page.tsx                # 保持，auth guard 改用 useAuthStore
��   ├── login/page.tsx          # 保持，改用 useAuthStore
│   └── service/page.tsx        # 保持（不在本次重构范围）
├── components/
│   ├── app-sidebar.tsx         # 新：左侧栏（sidebar17 模式）
│   ├── workspace-switcher.tsx  # 新：纯展示 workspace 信��
│   ├── nav-user.tsx            # 新：用户 footer
│   ├── directory-tree.tsx      # 新：Files tab 目录树
│   ├��─ session-list-panel.tsx  # 新：session 列表面板
│   ├── session-chat.tsx        # 新：会话消��区
│   ├── session-detail-panel.tsx# 新：右侧详情面板
│   └── ui/                     # 保持
├── stores/
│   ├── auth-store.ts           # 新
│   ├── workspace-store.ts      # 新
│   ├── session-store.ts        # 新
│   └��─ ui-store.ts             # 新
├── lib/
│   ├── types.ts                # 保持
│   ├── api.ts                  # 保持
│   ├── auth.tsx                # 删除（迁移到 auth-store）
│   └── utils.ts                # ���持
```

## 实现范围

**本次实现**：
- 四栏布局骨架
- Files tab 目录树导航
- Session 列表
- Session 消息展示（只读）
- Session 详情面板（只读）
- 创建 session 对话框
- Zustand stores（auth, workspace, session, ui）
- Auth 从 Context 迁移到 Zustand

**不实现**：
- Datas tab、Services tab（TODO 占位）
- 消息发送功能（输入框 UI only）
- 添加成员功能（按钮 UI only）
- Members/Providers/Harness/Service Inbox 视图（移除）
- 移动端适配

## API 代理

Next.js config 添加 rewrites，将 `/api/v1/*` 代理到 `http://localhost:3000/api/v1/*`。
