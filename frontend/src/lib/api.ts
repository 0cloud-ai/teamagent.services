import type {
  AuthResponse,
  UserWithMemberships,
  User,
  StatsResponse,
  SessionListResponse,
  Session,
  SessionMessagesResponse,
  SessionMember,
  Member,
  Provider,
  PingResult,
  HarnessResponse,
  Engine,
  Binding,
  Conversation,
  ConversationDetail,
  ConversationMessage,
  InboxConversation,
  InboxConversationDetail,
  ServiceInfo,
  DirectoryListing,
  FileContent,
  Message,
} from "./types";

// ── Base ────────────────────────────────────────────────────────────

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

// ── User ────────────────────────────────────────────────────────────

export const userApi = {
  register: (email: string, name: string, password: string) =>
    request<AuthResponse>("/api/v1/user/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/api/v1/user/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    request<{ message: string }>("/api/v1/user/logout", { method: "POST" }),

  getMe: () => request<UserWithMemberships>("/api/v1/user/me"),

  updateMe: (name: string) =>
    request<User>("/api/v1/user/me", {
      method: "PUT",
      body: JSON.stringify({ name }),
    }),

  changePassword: (oldPassword: string, newPassword: string) =>
    request<{ message: string }>("/api/v1/user/me/password", {
      method: "PUT",
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    }),
};

// ── Workspace: Stats ────────────────────────────────────────────────

export const statsApi = {
  get: (path = "/") =>
    request<StatsResponse>(
      `/api/v1/workspace/stats?path=${encodeURIComponent(path)}`,
    ),
};

// ── Workspace: Sessions ─────────────────────────────────────────────

export const sessionsApi = {
  list: (
    path: string,
    params?: { cursor?: string; limit?: number; sort?: string },
  ) => {
    const url =
      path === "/"
        ? "/api/v1/workspace/sessions"
        : `/api/v1/workspace/sessions${path}`;
    const qs = new URLSearchParams();
    if (params?.cursor) qs.set("cursor", params.cursor);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.sort) qs.set("sort", params.sort);
    const q = qs.toString();
    return request<SessionListResponse>(q ? `${url}?${q}` : url);
  },

  create: (data: {
    path: string;
    title?: string;
    harness?: string;
    members?: string[];
  }) =>
    request<Session>("/api/v1/workspace/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMessages: (
    sessionId: string,
    params?: { cursor?: string; limit?: number; order?: string },
  ) => {
    const qs = new URLSearchParams();
    if (params?.cursor) qs.set("cursor", params.cursor);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.order) qs.set("order", params.order);
    const q = qs.toString();
    return request<SessionMessagesResponse>(
      `/api/v1/workspace/sessions/${sessionId}/messages${q ? "?" + q : ""}`,
    );
  },

  sendMessage: (
    sessionId: string,
    content: string,
    mentions?: string[],
  ) =>
    request<Message>(
      `/api/v1/workspace/sessions/${sessionId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ content, mentions }),
      },
    ),

  listMembers: (sessionId: string) =>
    request<{ members: SessionMember[] }>(
      `/api/v1/workspace/sessions/${sessionId}/members`,
    ),

  addMember: (sessionId: string, memberId: string) =>
    request<SessionMember>(
      `/api/v1/workspace/sessions/${sessionId}/members`,
      { method: "POST", body: JSON.stringify({ member_id: memberId }) },
    ),

  removeMember: (sessionId: string, memberId: string) =>
    request<{ message: string }>(
      `/api/v1/workspace/sessions/${sessionId}/members/${memberId}`,
      { method: "DELETE" },
    ),
};

// ── Workspace: Files ────────────────────────────────────────────────

export const filesApi = {
  list: (sessionId: string, path = "/") =>
    request<DirectoryListing>(
      `/api/v1/workspace/sessions/${sessionId}/files/${path}`,
    ),

  read: (sessionId: string, path: string) =>
    request<FileContent>(
      `/api/v1/workspace/sessions/${sessionId}/files/${path}`,
    ),

  write: (sessionId: string, path: string, content: string) =>
    request<{ path: string; size: number; modified_at: string; event_id: string }>(
      `/api/v1/workspace/sessions/${sessionId}/files/${path}`,
      { method: "PUT", body: JSON.stringify({ content }) },
    ),

  create: (sessionId: string, path: string, content: string) =>
    request<{ path: string; size: number; modified_at: string; event_id: string }>(
      `/api/v1/workspace/sessions/${sessionId}/files/${path}`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),

  remove: (sessionId: string, path: string) =>
    request<{ path: string; event_id: string }>(
      `/api/v1/workspace/sessions/${sessionId}/files/${path}`,
      { method: "DELETE" },
    ),
};

// ── Workspace: Members ──────────────────────────────────────────────

export const membersApi = {
  list: (type?: string) => {
    const q = type ? `?type=${type}` : "";
    return request<{ members: Member[] }>(`/api/v1/workspace/members${q}`);
  },

  add: (data: {
    type: "user" | "service";
    name: string;
    email?: string;
    role?: string;
    service_url?: string;
  }) =>
    request<Member>("/api/v1/workspace/members", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (memberId: string, data: { name?: string; role?: string }) =>
    request<Member>(`/api/v1/workspace/members/${memberId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  remove: (memberId: string) =>
    request<{ message: string }>(`/api/v1/workspace/members/${memberId}`, {
      method: "DELETE",
    }),

  ping: (memberId: string) =>
    request<PingResult>(`/api/v1/workspace/members/${memberId}/ping`, {
      method: "POST",
    }),
};

// ── Workspace: Providers ────────────────────────────────────────────

export const providersApi = {
  list: () => request<{ providers: Provider[] }>("/api/v1/workspace/providers"),

  create: (data: {
    vendor: string;
    model: string;
    api_base?: string;
    api_key?: string;
  }) =>
    request<Provider>("/api/v1/workspace/providers", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (providerId: string, data: Record<string, unknown>) =>
    request<Provider>(`/api/v1/workspace/providers/${providerId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  remove: (providerId: string) =>
    request<{ message: string }>(`/api/v1/workspace/providers/${providerId}`, {
      method: "DELETE",
    }),

  ping: (providerId: string) =>
    request<PingResult>(`/api/v1/workspace/providers/${providerId}/ping`, {
      method: "POST",
    }),
};

// ── Workspace: Harness ──────────────────────────────────────────────

export const harnessApi = {
  get: () => request<HarnessResponse>("/api/v1/workspace/harness"),

  setDefault: (engineId: string) =>
    request<HarnessResponse>("/api/v1/workspace/harness/default", {
      method: "PUT",
      body: JSON.stringify({ engine_id: engineId }),
    }),

  getEngine: (engineId: string) =>
    request<Engine>(`/api/v1/workspace/harness/engines/${engineId}`),

  addBinding: (engineId: string, providerId: string, role = "default") =>
    request<Binding>(
      `/api/v1/workspace/harness/engines/${engineId}/bindings`,
      {
        method: "POST",
        body: JSON.stringify({ provider_id: providerId, role }),
      },
    ),

  updateBinding: (engineId: string, providerId: string, role: string) =>
    request<Binding>(
      `/api/v1/workspace/harness/engines/${engineId}/bindings/${providerId}`,
      { method: "PUT", body: JSON.stringify({ role }) },
    ),

  deleteBinding: (engineId: string, providerId: string) =>
    request<{ message: string }>(
      `/api/v1/workspace/harness/engines/${engineId}/bindings/${providerId}`,
      { method: "DELETE" },
    ),
};

// ── Workspace: Service Inbox ────────────────────────────────────────

export const serviceInboxApi = {
  list: (params?: { status?: string; label?: string; cursor?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.label) qs.set("label", params.label);
    if (params?.cursor) qs.set("cursor", params.cursor);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return request<{ conversations: InboxConversation[]; pagination: unknown }>(
      `/api/v1/workspace/service-inbox${q ? "?" + q : ""}`,
    );
  },

  getDetail: (conversationId: string) =>
    request<InboxConversationDetail>(
      `/api/v1/workspace/service-inbox/${conversationId}`,
    ),

  escalate: (conversationId: string, reason?: string) =>
    request<InboxConversationDetail>(
      `/api/v1/workspace/service-inbox/${conversationId}/escalate`,
      { method: "POST", body: JSON.stringify({ reason }) },
    ),

  close: (conversationId: string) =>
    request<InboxConversationDetail>(
      `/api/v1/workspace/service-inbox/${conversationId}/close`,
      { method: "POST" },
    ),

  reopen: (conversationId: string) =>
    request<InboxConversationDetail>(
      `/api/v1/workspace/service-inbox/${conversationId}/reopen`,
      { method: "POST" },
    ),

  updateLabels: (conversationId: string, labels: string[]) =>
    request<InboxConversationDetail>(
      `/api/v1/workspace/service-inbox/${conversationId}/labels`,
      { method: "PUT", body: JSON.stringify({ labels }) },
    ),
};

// ── Service: Info ───────────────────────────────────────────────────

export const serviceInfoApi = {
  get: () => request<ServiceInfo>("/api/v1/service/info"),

  update: (data: Partial<ServiceInfo>) =>
    request<ServiceInfo>("/api/v1/service/info", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// ── Service: Conversations ──────────────────────────────────────────

export const conversationsApi = {
  list: (params?: { status?: string; label?: string; cursor?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.label) qs.set("label", params.label);
    if (params?.cursor) qs.set("cursor", params.cursor);
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return request<{ conversations: Conversation[]; pagination: unknown }>(
      `/api/v1/service/conversations${q ? "?" + q : ""}`,
    );
  },

  create: (message: string, labels?: string[]) =>
    request<{ conversation: Conversation; message: ConversationMessage }>(
      "/api/v1/service/conversations",
      { method: "POST", body: JSON.stringify({ message, labels }) },
    ),

  getDetail: (conversationId: string, params?: { cursor?: string; limit?: number; order?: string }) => {
    const qs = new URLSearchParams();
    if (params?.cursor) qs.set("cursor", params.cursor);
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.order) qs.set("order", params.order);
    const q = qs.toString();
    return request<ConversationDetail>(
      `/api/v1/service/conversations/${conversationId}${q ? "?" + q : ""}`,
    );
  },

  sendMessage: (conversationId: string, content: string) =>
    request<ConversationMessage>(
      `/api/v1/service/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify({ content }) },
    ),

  updateLabels: (conversationId: string, labels: string[]) =>
    request<Conversation>(
      `/api/v1/service/conversations/${conversationId}/labels`,
      { method: "PUT", body: JSON.stringify({ labels }) },
    ),

  close: (conversationId: string) =>
    request<Conversation>(
      `/api/v1/service/conversations/${conversationId}/close`,
      { method: "POST" },
    ),
};
