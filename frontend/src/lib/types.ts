// ── Pagination ──────────────────────────────────────────────────────

export type Pagination = {
  next_cursor: string | null;
  has_more: boolean;
  total: number;
};

// ── User ────────────────────────────────────────────────────────────

export type User = {
  id: string;
  email: string;
  name: string;
  created_at: string;
};

export type Membership = {
  member_id: string;
  workspace_name: string;
  workspace_url: string;
  role: string;
};

export type UserWithMemberships = User & {
  memberships: Membership[];
};

export type AuthResponse = {
  token: string;
  user: User;
};

// ── Stats ───────────────────────────────────────────────────────────

export type Counts = {
  directories: number;
  sessions: number;
  messages: number;
};

export type ChildStats = {
  name: string;
  total: Counts;
};

export type StatsResponse = {
  path: string;
  direct: Counts;
  total: Counts;
  children: ChildStats[];
};

// ── Sessions ────────────────────────────────────────────────────────

export type Session = {
  id: string;
  title: string;
  path?: string;
  harness: string;
  members: string[];
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type SessionListResponse = {
  path: string;
  sessions: Session[];
  pagination: Pagination;
};

// ── Messages / Events ───────────────────────────────────────────────

export type Message = {
  id: string;
  type: "message" | "event";
  role?: string;
  content?: string;
  actor?: string;
  action?: string;
  target?: string;
  detail?: string;
  created_at: string;
};

export type SessionMessagesResponse = {
  session_id: string;
  session: Session;
  messages: Message[];
  pagination: Pagination;
};

// ── Session Members ─────────────────────────────────────────────────

export type SessionMember = {
  id: string;
  type: string;
  name: string;
  service_url?: string;
  status?: string;
  joined_at: string;
  joined_via: string;
};

// ── Members ─────────────────────────────────────────────────────────

export type Member = {
  id: string;
  type: "user" | "service";
  name: string;
  email?: string;
  role?: string;
  service_url?: string;
  service_info?: Record<string, unknown>;
  status?: string;
  joined_at: string;
};

// ── Providers ───────────────────────────────────────────────────────

export type Provider = {
  id: string;
  vendor: string;
  model: string;
  api_base: string;
  status: string;
  used_by: string[];
  created_at: string;
};

export type PingResult = {
  status: string;
  latency_ms?: number;
  model?: string;
  message?: string;
  error?: string;
};

// ── Harness ─────────────────────────────────────────────────────────

export type Binding = {
  provider_id: string;
  vendor: string;
  model: string;
  role: string;
};

export type Engine = {
  id: string;
  name: string;
  description: string;
  supported_vendors: string[];
  bindings: Binding[];
};

export type HarnessResponse = {
  default: string;
  engines: Engine[];
};

// ── Conversations (Service) ─────────────────────────────────────────

export type Conversation = {
  id: string;
  title: string;
  status: "open" | "escalated" | "closed";
  labels: string[];
  closed_at?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ConversationDetail = Conversation & {
  messages: ConversationMessage[];
  pagination?: Pagination;
};

// ── Service Inbox ───────────────────────────────────────────────────

export type ConsumerInfo = {
  user_id: string;
  name: string;
};

export type SessionRef = {
  session_id: string;
  session_title: string;
};

export type InboxConversation = {
  id: string;
  title: string;
  consumer: ConsumerInfo;
  status: "open" | "escalated" | "closed";
  labels: string[];
  closed_at?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type InboxConversationDetail = InboxConversation & {
  messages: ConversationMessage[];
  referenced_by: SessionRef[];
  pagination?: Pagination;
};

// ── Service Info ────────────────────────────────────────────────────

export type ServiceInfo = {
  name: string;
  description: string;
  status: string;
  capabilities: string[];
};

// ── File Browser ────────────────────────────────────────────────────

export type FileEntry = {
  name: string;
  type: "file" | "directory";
  size?: number;
  modified_at?: string;
};

export type DirectoryListing = {
  path: string;
  entries: FileEntry[];
};

export type FileContent = {
  path: string;
  type: "file";
  size: number;
  modified_at: string;
  content: string;
};
