# 前端重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将前端重构为 sidebar17 + application-shell10 风格的四栏布局，使用 Zustand 状态管理。

**Architecture:** 左侧栏（sidebar17 模式：workspace 展示 + tabs + 目录树 + 用户信息） + SidebarInset 内三列（session 列表 + 聊天区 + 详情面板）。Zustand 替换 React Context 管理 auth/workspace/session/ui 状态。

**Tech Stack:** Next.js 16, React 19, shadcn/ui, Zustand, Tailwind CSS v4, lucide-react

**参考文件：**
- 左侧栏布局：`/home/twwyzh/shadcnblocks-blocks/block/sidebar17.tsx`
- 主内容区布局：`/home/twwyzh/shadcnblocks-blocks/block/application-shell10.tsx`
- 设计文档：`docs/superpowers/specs/2026-04-05-frontend-refactor-design.md`

**API 文档：** `docs/api/` 目录下的所有文档

**现有 shadcn 组件：** avatar, badge, button, command, dialog, drawer, dropdown-menu, input, input-group, scroll-area, separator, sheet, sidebar, skeleton, textarea, tooltip

**需要新增的 shadcn 组件：** tabs

**后端：** 已运行在 localhost:3000，当前 next.config.ts 的 rewrites 指向 8000，需改为 3000

---

### Task 1: 安装依赖 + 添加缺失的 shadcn 组件 + 修复 API 代理

**Files:**
- Modify: `frontend/package.json` (添加 zustand)
- Modify: `frontend/next.config.ts` (修改代理端口)
- Create: `frontend/src/components/ui/tabs.tsx` (通过 shadcn CLI)

- [ ] **Step 1: 安装 Zustand**

```bash
cd /home/twwyzh/teamagent.services/frontend && npm install zustand
```

- [ ] **Step 2: 添加 shadcn tabs 组件**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx shadcn@latest add tabs
```

- [ ] **Step 3: 修改 next.config.ts 代理端口**

将 `frontend/next.config.ts` 中的 `http://localhost:8000` 改为 `http://localhost:3000`。

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:3000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 4: 验证**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -5
```

Expected: 构建成功，无报错。

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/next.config.ts frontend/src/components/ui/tabs.tsx
git commit -m "chore: add zustand + tabs component, fix API proxy port"
```

---

### Task 2: 创建 Zustand Stores

**Files:**
- Create: `frontend/src/stores/auth-store.ts`
- Create: `frontend/src/stores/workspace-store.ts`
- Create: `frontend/src/stores/session-store.ts`
- Create: `frontend/src/stores/ui-store.ts`

- [ ] **Step 1: 创建 auth-store.ts**

```ts
import { create } from "zustand";
import { userApi } from "@/lib/api";
import type { UserWithMemberships } from "@/lib/types";

type AuthState = {
  user: UserWithMemberships | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  validateToken: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  isLoading: true,

  login: async (email, password) => {
    const res = await userApi.login(email, password);
    localStorage.setItem("token", res.token);
    set({ token: res.token });
    const me = await userApi.getMe();
    set({ user: me });
  },

  register: async (email, name, password) => {
    const res = await userApi.register(email, name, password);
    localStorage.setItem("token", res.token);
    set({ token: res.token });
    const me = await userApi.getMe();
    set({ user: me });
  },

  logout: () => {
    userApi.logout().catch(() => {});
    localStorage.removeItem("token");
    set({ user: null, token: null });
  },

  validateToken: async () => {
    const stored = localStorage.getItem("token");
    if (!stored) {
      set({ isLoading: false });
      return;
    }
    set({ token: stored });
    try {
      const me = await userApi.getMe();
      set({ user: me, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null, isLoading: false });
    }
  },
}));
```

- [ ] **Step 2: 创建 workspace-store.ts**

```ts
import { create } from "zustand";
import { statsApi, sessionsApi } from "@/lib/api";
import type { ChildStats, Session } from "@/lib/types";

type WorkspaceState = {
  currentPath: string;
  children: ChildStats[];
  sessions: Session[];
  isLoadingSessions: boolean;
  setPath: (path: string) => void;
  fetchStats: (path?: string) => Promise<void>;
  fetchSessions: (path?: string) => Promise<void>;
};

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  currentPath: "/",
  children: [],
  sessions: [],
  isLoadingSessions: false,

  setPath: (path) => {
    set({ currentPath: path });
    get().fetchStats(path);
    get().fetchSessions(path);
  },

  fetchStats: async (path) => {
    const p = path ?? get().currentPath;
    try {
      const data = await statsApi.get(p);
      set({ children: data.children });
    } catch {
      set({ children: [] });
    }
  },

  fetchSessions: async (path) => {
    const p = path ?? get().currentPath;
    set({ isLoadingSessions: true });
    try {
      const data = await sessionsApi.list(p);
      set({ sessions: data.sessions, isLoadingSessions: false });
    } catch {
      set({ sessions: [], isLoadingSessions: false });
    }
  },
}));
```

- [ ] **Step 3: 创建 session-store.ts**

```ts
import { create } from "zustand";
import { sessionsApi } from "@/lib/api";
import type { Message, SessionMember, Session } from "@/lib/types";

type SessionState = {
  selectedSession: Session | null;
  messages: Message[];
  members: SessionMember[];
  isLoadingMessages: boolean;
  selectSession: (session: Session) => void;
  clearSession: () => void;
  fetchMessages: (sessionId?: string) => Promise<void>;
  fetchMembers: (sessionId?: string) => Promise<void>;
};

export const useSessionStore = create<SessionState>((set, get) => ({
  selectedSession: null,
  messages: [],
  members: [],
  isLoadingMessages: false,

  selectSession: (session) => {
    set({ selectedSession: session, messages: [], members: [] });
    get().fetchMessages(session.id);
    get().fetchMembers(session.id);
  },

  clearSession: () => {
    set({ selectedSession: null, messages: [], members: [] });
  },

  fetchMessages: async (sessionId) => {
    const id = sessionId ?? get().selectedSession?.id;
    if (!id) return;
    set({ isLoadingMessages: true });
    try {
      const data = await sessionsApi.getMessages(id);
      set({ messages: data.messages, isLoadingMessages: false });
    } catch {
      set({ messages: [], isLoadingMessages: false });
    }
  },

  fetchMembers: async (sessionId) => {
    const id = sessionId ?? get().selectedSession?.id;
    if (!id) return;
    try {
      const data = await sessionsApi.listMembers(id);
      set({ members: data.members });
    } catch {
      set({ members: [] });
    }
  },
}));
```

- [ ] **Step 4: 创建 ui-store.ts**

```ts
import { create } from "zustand";

type ActiveTab = "files" | "datas" | "services";

type UIState = {
  activeTab: ActiveTab;
  isDetailPanelOpen: boolean;
  setActiveTab: (tab: ActiveTab) => void;
  toggleDetailPanel: () => void;
  setDetailPanelOpen: (open: boolean) => void;
};

export const useUIStore = create<UIState>((set) => ({
  activeTab: "files",
  isDetailPanelOpen: true,

  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleDetailPanel: () => set((s) => ({ isDetailPanelOpen: !s.isDetailPanelOpen })),
  setDetailPanelOpen: (open) => set({ isDetailPanelOpen: open }),
}));
```

- [ ] **Step 5: 验证构建**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -5
```

Expected: 构建成功。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add Zustand stores (auth, workspace, session, ui)"
```

---

### Task 3: 迁移 Auth 到 Zustand + 更新 layout/page/login

**Files:**
- Modify: `frontend/src/app/layout.tsx` (移除 AuthProvider)
- Modify: `frontend/src/app/page.tsx` (改用 useAuthStore)
- Modify: `frontend/src/app/login/page.tsx` (改用 useAuthStore)
- Delete: `frontend/src/lib/auth.tsx`

- [ ] **Step 1: 修改 layout.tsx — 移除 AuthProvider**

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TeamAgent Service",
  description: "AI Agent Service Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 2: 修改 page.tsx — 改用 useAuthStore**

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function Home() {
  const { user, isLoading, validateToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  // WorkspaceShell 将在 Task 4 中创建，此处先占位
  return <div>Workspace placeholder</div>;
}
```

- [ ] **Step 3: 修改 login/page.tsx — 改用 useAuthStore**

```tsx
"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type Tab = "login" | "register";

export default function LoginPage() {
  const { user, isLoading, login, register, validateToken } = useAuthStore();
  const router = useRouter();

  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/");
    }
  }, [isLoading, user, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        await register(email, name, password);
      }
      router.replace("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  function switchTab(next: Tab) {
    setTab(next);
    setError(null);
  }

  if (isLoading) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight">
            TeamAgent Service
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {tab === "login"
              ? "Sign in to your account"
              : "Create a new account"}
          </p>
        </div>

        <div className="flex rounded-lg border border-border bg-muted p-0.5">
          <button
            type="button"
            onClick={() => switchTab("login")}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === "login"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => switchTab("register")}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === "register"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium leading-none">
              Email
            </label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          {tab === "register" && (
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium leading-none">
                Name
              </label>
              <Input
                id="name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium leading-none">
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete={tab === "login" ? "current-password" : "new-password"}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" className="w-full" size="lg" disabled={submitting}>
            {submitting
              ? tab === "login" ? "Signing in..." : "Creating account..."
              : tab === "login" ? "Sign in" : "Create account"}
          </Button>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 删除旧的 auth.tsx**

```bash
rm frontend/src/lib/auth.tsx
```

- [ ] **Step 5: 验证构建**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -10
```

Expected: 构建成功，无引用 `@/lib/auth` 的错误。

- [ ] **Step 6: Commit**

```bash
git add -A frontend/src/app/ frontend/src/lib/auth.tsx
git commit -m "refactor: migrate auth from React Context to Zustand"
```

---

### Task 4: 创建左侧栏组件（sidebar17 模式）

**Files:**
- Create: `frontend/src/components/workspace-switcher.tsx`
- Create: `frontend/src/components/nav-user.tsx`
- Create: `frontend/src/components/directory-tree.tsx`
- Create: `frontend/src/components/app-sidebar.tsx`

**参考:** 直接参照 `/home/twwyzh/shadcnblocks-blocks/block/sidebar17.tsx` 的 `WorkspaceSwitcher`、`NavUser`、`NavList`、`AppSidebar` 组件结构，将 mock 数据替换为真实 store 数据。

- [ ] **Step 1: 创建 workspace-switcher.tsx**

纯展示组件。从 sidebar17 的 `WorkspaceSwitcher` 简化而来，去掉下拉切换，保留样式。

```tsx
"use client";

import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";

export function WorkspaceSwitcher() {
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="lg"
          className="cursor-default hover:bg-transparent"
        >
          <div className="flex aspect-square size-8 items-center justify-center rounded-sm bg-primary">
            <span className="text-sm font-bold text-primary-foreground">T</span>
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-medium">TeamAgent</span>
            <span className="truncate text-xs text-muted-foreground">
              AI Agent Service
            </span>
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
```

- [ ] **Step 2: 创建 nav-user.tsx**

从 sidebar17 的 `NavUser` 复制，接入 useAuthStore。

```tsx
"use client";

import { ChevronsUpDown, LogOut, User } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from "@/components/ui/sidebar";
import { useAuthStore } from "@/stores/auth-store";

export function NavUser() {
  const { user, logout } = useAuthStore();

  if (!user) return null;

  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="size-8 rounded-lg">
                <AvatarFallback className="rounded-lg">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{user.name}</span>
                <span className="truncate text-xs text-muted-foreground">
                  {user.email}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            side="bottom"
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <Avatar className="size-8 rounded-lg">
                  <AvatarFallback className="rounded-lg">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{user.name}</span>
                  <span className="truncate text-xs text-muted-foreground">
                    {user.email}
                  </span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 size-4" />
              Account
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>
              <LogOut className="mr-2 size-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
```

- [ ] **Step 3: 创建 directory-tree.tsx**

Files tab 的目录树内容。使用 useWorkspaceStore。

```tsx
"use client";

import { useEffect } from "react";
import { FolderOpen, ChevronLeft } from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuBadge,
} from "@/components/ui/sidebar";
import { useWorkspaceStore } from "@/stores/workspace-store";

export function DirectoryTree() {
  const { currentPath, children, setPath, fetchStats } = useWorkspaceStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const isRoot = currentPath === "/";

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Explorer</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {!isRoot && (
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => {
                  const parent = currentPath.replace(/\/[^/]+\/?$/, "") || "/";
                  setPath(parent);
                }}
              >
                <ChevronLeft className="size-4" />
                <span>..</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )}
          <SidebarMenuItem>
            <SidebarMenuButton isActive>
              <FolderOpen className="size-4" />
              <span>{currentPath === "/" ? "/" : currentPath.split("/").pop()}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          {children.map((child) => (
            <SidebarMenuItem key={child.name}>
              <SidebarMenuButton
                onClick={() => {
                  const next = currentPath === "/"
                    ? `/${child.name}`
                    : `${currentPath}/${child.name}`;
                  setPath(next);
                }}
                className="pl-6"
              >
                <FolderOpen className="size-4" />
                <span>{child.name}</span>
                {child.total.sessions > 0 && (
                  <SidebarMenuBadge>{child.total.sessions}</SidebarMenuBadge>
                )}
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
```

- [ ] **Step 4: 创建 app-sidebar.tsx**

组装以上组件，参照 sidebar17 的 AppSidebar 结构。

```tsx
"use client";

import * as React from "react";
import { FolderOpen, Database, Plug } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { WorkspaceSwitcher } from "@/components/workspace-switcher";
import { NavUser } from "@/components/nav-user";
import { DirectoryTree } from "@/components/directory-tree";
import { useUIStore } from "@/stores/ui-store";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { activeTab, setActiveTab } = useUIStore();

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <WorkspaceSwitcher />
        <Tabs
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as "files" | "datas" | "services")}
          className="w-full"
        >
          <TabsList className="w-full">
            <TabsTrigger value="files" className="flex-1">
              <FolderOpen className="size-4" />
            </TabsTrigger>
            <TabsTrigger value="datas" className="flex-1">
              <Database className="size-4" />
            </TabsTrigger>
            <TabsTrigger value="services" className="flex-1">
              <Plug className="size-4" />
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </SidebarHeader>
      <SidebarContent>
        {activeTab === "files" && <DirectoryTree />}
        {activeTab === "datas" && (
          <div className="flex flex-1 items-center justify-center p-4 text-sm text-muted-foreground">
            Datas — TODO
          </div>
        )}
        {activeTab === "services" && (
          <div className="flex flex-1 items-center justify-center p-4 text-sm text-muted-foreground">
            Services — TODO
          </div>
        )}
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
```

- [ ] **Step 5: 验证构建**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -10
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/workspace-switcher.tsx frontend/src/components/nav-user.tsx frontend/src/components/directory-tree.tsx frontend/src/components/app-sidebar.tsx
git commit -m "feat: add sidebar components (workspace-switcher, nav-user, directory-tree, app-sidebar)"
```

---

### Task 5: 创建主内容区三个面板

**Files:**
- Create: `frontend/src/components/session-list-panel.tsx`
- Create: `frontend/src/components/session-chat.tsx`
- Create: `frontend/src/components/session-detail-panel.tsx`

**参考:** 直接参照 `/home/twwyzh/shadcnblocks-blocks/block/application-shell10.tsx` 的 `TicketListPanel`、消息区、`InboxAgentPanel` 结构。

- [ ] **Step 1: 创建 session-list-panel.tsx**

参照 shell10 的 TicketListPanel。

```tsx
"use client";

import { useEffect } from "react";
import { Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/stores/workspace-store";
import { useSessionStore } from "@/stores/session-store";
import type { Session } from "@/lib/types";

export function SessionListPanel() {
  const { currentPath, sessions, isLoadingSessions, fetchSessions } =
    useWorkspaceStore();
  const { selectedSession, selectSession } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions, currentPath]);

  return (
    <div className="flex h-full w-1/4 max-w-[320px] min-w-[240px] shrink-0 flex-col overflow-hidden border-r bg-background">
      <div className="flex h-14 shrink-0 items-center justify-between border-b px-4">
        <div className="truncate text-sm font-medium text-foreground">
          {currentPath}
        </div>
        <Button variant="ghost" size="icon" className="size-7 shrink-0">
          <Plus className="size-4" />
        </Button>
      </div>
      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        {isLoadingSessions ? (
          <div className="p-4 text-sm text-muted-foreground">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No sessions in this directory
          </div>
        ) : (
          sessions.map((session) => (
            <SessionItem
              key={session.id}
              session={session}
              isSelected={selectedSession?.id === session.id}
              onSelect={() => selectSession(session)}
            />
          ))
        )}
      </ScrollArea>
    </div>
  );
}

function SessionItem({
  session,
  isSelected,
  onSelect,
}: {
  session: Session;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full border-b p-4 text-left text-sm leading-tight last:border-b-0 hover:bg-muted/50",
        isSelected && "bg-muted",
      )}
    >
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate font-medium">{session.title}</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Harness: {session.harness}
        </p>
        <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <MessageSquare className="size-3" />
          <span>{session.message_count} messages</span>
          <span className="ml-auto">
            {new Date(session.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </button>
  );
}
```

- [ ] **Step 2: 创建 session-chat.tsx**

参照 shell10 的消息区域 + ReplyComposer。

```tsx
"use client";

import { PanelRight, MessageSquare, Send } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/stores/session-store";
import { useUIStore } from "@/stores/ui-store";
import type { Message } from "@/lib/types";

export function SessionChat() {
  const { selectedSession, messages, isLoadingMessages } = useSessionStore();
  const { isDetailPanelOpen, toggleDetailPanel } = useUIStore();

  if (!selectedSession) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <div className="text-center">
          <MessageSquare className="mx-auto size-12 opacity-50" />
          <p className="mt-2 text-sm">Select a session to view</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background px-4">
        <div className="flex items-center gap-3">
          <MessageSquare className="size-5" />
          <span className="font-medium">{selectedSession.title}</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={toggleDetailPanel}
        >
          <PanelRight
            className={cn("size-4", isDetailPanelOpen && "text-primary")}
          />
        </Button>
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <div className="px-6 py-6 lg:px-10">
          <div className="mx-auto max-w-3xl space-y-8">
            {isLoadingMessages ? (
              <p className="text-sm text-muted-foreground">Loading messages...</p>
            ) : messages.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center">
                No messages yet
              </p>
            ) : (
              messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))
            )}
          </div>
        </div>
      </ScrollArea>

      <div className="shrink-0 border-t bg-background px-6 py-4 lg:px-10">
        <div className="mx-auto max-w-3xl rounded-lg border bg-muted/30">
          <Textarea
            placeholder="Write a message..."
            className="min-h-[80px] resize-none border-0 bg-transparent focus-visible:ring-0"
            disabled
          />
          <div className="flex items-center justify-end gap-2 border-t px-3 py-2">
            <Button size="sm" className="gap-1" disabled>
              <Send className="size-3" />
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.type === "event") {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
          {message.action}
        </Badge>
        <span>{message.actor}</span>
        {message.target && (
          <span className="font-mono text-[11px]">{message.target}</span>
        )}
        {message.detail && <span>— {message.detail}</span>}
      </div>
    );
  }

  const isAssistant = message.role === "assistant";

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        <Avatar className="mt-0.5 size-10 shrink-0">
          <AvatarFallback className="bg-primary text-xs font-medium text-primary-foreground">
            {isAssistant ? "AI" : "U"}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">
              {isAssistant ? "Assistant" : "User"}
            </span>
            {isAssistant && (
              <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
                AI
              </Badge>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date(message.created_at).toLocaleString()}
          </span>
        </div>
      </div>
      <div className="pl-13 text-sm leading-relaxed whitespace-pre-wrap">
        {message.content}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 session-detail-panel.tsx**

参照 shell10 的 InboxAgentPanel，群聊 settings 风格。

```tsx
"use client";

import { Info, UserPlus } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useSessionStore } from "@/stores/session-store";

export function SessionDetailPanel() {
  const { selectedSession, members } = useSessionStore();

  if (!selectedSession) return null;

  return (
    <div className="flex h-full w-1/4 max-w-[360px] min-w-[280px] shrink-0 flex-col overflow-hidden border-l bg-background">
      <div className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <Info className="size-4" />
        <span className="font-semibold">Session Details</span>
      </div>
      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        <div className="space-y-6 p-4">
          {/* Session Info */}
          <section className="space-y-3">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Information
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Harness</span>
                <span>{selectedSession.harness}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Messages</span>
                <span>{selectedSession.message_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created</span>
                <span>
                  {new Date(selectedSession.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Updated</span>
                <span>
                  {new Date(selectedSession.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </section>

          {/* Members */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Members ({members.length})
              </p>
              <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs" disabled>
                <UserPlus className="size-3" />
                Add
              </Button>
            </div>
            <div className="space-y-1">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center gap-3 rounded-md p-2 hover:bg-muted"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="text-xs">
                      {member.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {member.name}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <span>{member.joined_via}</span>
                      {member.type !== "user" && (
                        <Badge
                          variant="outline"
                          className="h-4 px-1 text-[10px]"
                        >
                          {member.type}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {members.length === 0 && (
                <p className="text-sm text-muted-foreground">No members</p>
              )}
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}
```

- [ ] **Step 4: 验证构建**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -10
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/session-list-panel.tsx frontend/src/components/session-chat.tsx frontend/src/components/session-detail-panel.tsx
git commit -m "feat: add session panels (list, chat, detail)"
```

---

### Task 6: 组装主页面 + 清理旧组件

**Files:**
- Rewrite: `frontend/src/app/page.tsx` (接入完整布局)
- Delete: `frontend/src/components/workspace-shell.tsx`
- Delete: `frontend/src/components/file-browser.tsx`
- Delete: `frontend/src/components/application-shell.tsx`
- Delete: `frontend/src/components/workspace/sessions-view.tsx`
- Delete: `frontend/src/components/workspace/members-view.tsx`
- Delete: `frontend/src/components/workspace/providers-view.tsx`
- Delete: `frontend/src/components/workspace/harness-view.tsx`
- Delete: `frontend/src/components/workspace/service-inbox-view.tsx`

- [ ] **Step 1: 重写 page.tsx — 四栏布局**

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SessionListPanel } from "@/components/session-list-panel";
import { SessionChat } from "@/components/session-chat";
import { SessionDetailPanel } from "@/components/session-detail-panel";

export default function Home() {
  const { user, isLoading, validateToken } = useAuthStore();
  const { isDetailPanelOpen } = useUIStore();
  const router = useRouter();

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-0 overflow-hidden">
        <div className="flex h-full w-full">
          <SessionListPanel />
          <SessionChat />
          {isDetailPanelOpen && <SessionDetailPanel />}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

- [ ] **Step 2: 删除旧组件**

```bash
rm frontend/src/components/workspace-shell.tsx
rm frontend/src/components/file-browser.tsx
rm -f frontend/src/components/application-shell.tsx
rm -rf frontend/src/components/workspace/
```

- [ ] **Step 3: 验证构建**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build 2>&1 | tail -10
```

Expected: 构建成功。如果 `application-shell.tsx` 或 `file-browser.tsx` 不存在，`rm -f` 会静默跳过。

- [ ] **Step 4: 验证页面运行**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next dev &
sleep 3
curl -s http://localhost:3001 | head -20
kill %1 2>/dev/null
```

Expected: 页面返回 HTML 内容。

- [ ] **Step 5: Commit**

```bash
git add -A frontend/src/
git commit -m "feat: assemble four-column layout, remove old workspace components"
```

---

### Task 7: 最终验证 + 清理

**Files:**
- Possibly modify: any file with build errors

- [ ] **Step 1: 完整构建验证**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next build
```

Expected: 构建成功，无错误。

- [ ] **Step 2: Lint 检查**

```bash
cd /home/twwyzh/teamagent.services/frontend && npx next lint
```

修复任何 lint 错误。

- [ ] **Step 3: 如有修复则 Commit**

```bash
git add -A frontend/src/
git commit -m "fix: resolve build/lint issues"
```
