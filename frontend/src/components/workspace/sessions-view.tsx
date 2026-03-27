"use client";

import * as React from "react";
import {
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Home,
  Loader2,
  MessageSquare,
  Plus,
  ArrowLeft,
  Send,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { statsApi, sessionsApi } from "@/lib/api";
import type {
  StatsResponse,
  ChildStats,
  Counts,
  Session,
  SessionListResponse,
  Message,
  SessionMessagesResponse,
} from "@/lib/types";

// ── Helpers ─────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Tree Node ───────────────────────────────────────────────────────

function TreeNode({
  name,
  path,
  total,
  activePath,
  onSelect,
}: {
  name: string;
  path: string;
  total: Counts;
  activePath: string;
  onSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = React.useState(false);
  const [children, setChildren] = React.useState<ChildStats[] | null>(null);
  const [loading, setLoading] = React.useState(false);
  const isActive = activePath === path;

  const handleExpand = async () => {
    if (!expanded && children === null) {
      setLoading(true);
      try {
        const data = await statsApi.get(path);
        setChildren(data.children);
      } catch {
        // ignore fetch errors
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  const hasChildren = total.directories > 0;
  const Icon = expanded ? FolderOpen : Folder;

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50 cursor-pointer",
          isActive && "bg-muted font-medium",
        )}
      >
        <button
          type="button"
          className="shrink-0 p-0.5"
          onClick={handleExpand}
        >
          {loading ? (
            <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
          ) : hasChildren ? (
            expanded ? (
              <ChevronDown className="size-3.5 text-muted-foreground" />
            ) : (
              <ChevronRight className="size-3.5 text-muted-foreground" />
            )
          ) : (
            <span className="inline-block size-3.5" />
          )}
        </button>
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-1.5"
          onClick={() => onSelect(path)}
        >
          <Icon className="size-4 shrink-0 text-blue-500" />
          <span className="truncate">{name}</span>
          <span className="ml-auto shrink-0 text-xs text-muted-foreground">
            {total.sessions}
          </span>
        </button>
      </div>
      {expanded && children && children.length > 0 && (
        <div className="ml-4 border-l pl-1">
          {children.map((child) => (
            <TreeNode
              key={child.name}
              name={child.name}
              path={`${path}/${child.name}`}
              total={child.total}
              activePath={activePath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Directory Tree ──────────────────────────────────────────────────

function DirectoryTree({
  activePath,
  onSelect,
}: {
  activePath: string;
  onSelect: (path: string) => void;
}) {
  const [rootStats, setRootStats] = React.useState<StatsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await statsApi.get("/");
        if (!cancelled) setRootStats(data);
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!rootStats) return null;

  return (
    <div className="flex flex-col gap-0.5 p-2">
      <div
        className={cn(
          "flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50 cursor-pointer",
          activePath === "/" && "bg-muted font-medium",
        )}
        onClick={() => onSelect("/")}
      >
        <Home className="size-4 shrink-0" />
        <span>All Sessions</span>
        <span className="ml-auto text-xs text-muted-foreground">
          {rootStats.total.sessions}
        </span>
      </div>
      {rootStats.children.map((child) => (
        <TreeNode
          key={child.name}
          name={child.name}
          path={`/${child.name}`}
          total={child.total}
          activePath={activePath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ── Breadcrumbs ─────────────────────────────────────────────────────

function Breadcrumbs({
  path,
  onNavigate,
}: {
  path: string;
  onNavigate: (path: string) => void;
}) {
  const segments = path === "/" ? [] : path.replace(/^\//, "").split("/");

  return (
    <div className="flex items-center gap-1 text-sm">
      <Button
        variant="ghost"
        size="sm"
        className="h-7 gap-1 px-2"
        onClick={() => onNavigate("/")}
      >
        <Home className="size-3.5" />
        <span>root</span>
      </Button>
      {segments.map((seg, i) => {
        const p = "/" + segments.slice(0, i + 1).join("/");
        const isLast = i === segments.length - 1;
        return (
          <React.Fragment key={p}>
            <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 px-2",
                isLast && "font-medium text-foreground",
              )}
              onClick={() => onNavigate(p)}
            >
              {seg}
            </Button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Create Session Form ─────────────────────────────────────────────

function CreateSessionForm({
  path,
  onCreated,
  onCancel,
}: {
  path: string;
  onCreated: (session: Session) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = React.useState("");
  const [harness, setHarness] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const session = await sessionsApi.create({
        path,
        title: title.trim(),
        harness: harness.trim() || undefined,
      });
      onCreated(session);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border rounded-lg p-4 m-4 space-y-3">
      <h3 className="text-sm font-medium">New Session</h3>
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-2 text-xs text-destructive">
          {error}
        </div>
      )}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Session title..."
          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
          autoFocus
        />
      </div>
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">Harness (optional)</label>
        <input
          type="text"
          value={harness}
          onChange={(e) => setHarness(e.target.value)}
          placeholder="e.g. claude-code"
          className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Button type="submit" size="sm" disabled={submitting || !title.trim()}>
          {submitting && <Loader2 className="size-3.5 animate-spin" />}
          Create
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

// ── Session List ────────────────────────────────────────────────────

function SessionList({
  path,
  onSelectSession,
}: {
  path: string;
  onSelectSession: (session: Session) => void;
}) {
  const [data, setData] = React.useState<SessionListResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [loadingMore, setLoadingMore] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [showCreate, setShowCreate] = React.useState(false);

  const fetchSessions = React.useCallback(async (p: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await sessionsApi.list(p, { limit: 20 });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch sessions");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchSessions(path);
  }, [path, fetchSessions]);

  const loadMore = async () => {
    if (!data?.pagination.next_cursor) return;
    setLoadingMore(true);
    try {
      const more = await sessionsApi.list(path, {
        cursor: data.pagination.next_cursor,
        limit: 20,
      });
      setData({
        ...more,
        sessions: [...data.sessions, ...more.sessions],
      });
    } catch {
      // ignore
    } finally {
      setLoadingMore(false);
    }
  };

  const handleCreated = (session: Session) => {
    setShowCreate(false);
    if (data) {
      setData({
        ...data,
        sessions: [session, ...data.sessions],
        pagination: {
          ...data.pagination,
          total: data.pagination.total + 1,
        },
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* New Session button */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <span className="text-xs text-muted-foreground">
          {data?.pagination.total ?? 0} session{(data?.pagination.total ?? 0) !== 1 ? "s" : ""}
        </span>
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={() => setShowCreate(!showCreate)}
        >
          <Plus className="size-3.5" />
          New Session
        </Button>
      </div>

      {showCreate && (
        <CreateSessionForm
          path={path}
          onCreated={handleCreated}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {!data || data.sessions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <MessageSquare className="size-12 opacity-50" />
          <p className="mt-2 text-sm">No sessions in this directory</p>
        </div>
      ) : (
        <>
          {data.sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              className="flex flex-col gap-1 border-b px-4 py-3 hover:bg-muted/30 text-left transition-colors"
              onClick={() => onSelectSession(session)}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-medium leading-snug">
                  {session.title}
                </span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {timeAgo(session.updated_at)}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                {session.harness && (
                  <span className="rounded-full bg-muted px-2 py-0.5 font-medium">
                    {session.harness}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <MessageSquare className="size-3" />
                  {session.message_count}
                </span>
              </div>
            </button>
          ))}
          {data.pagination.has_more && (
            <div className="p-4">
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={loadMore}
                disabled={loadingMore}
              >
                {loadingMore && <Loader2 className="size-3.5 animate-spin" />}
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Session Detail ──────────────────────────────────────────────────

type DetailTab = "chat" | "files" | "terminal";

function SessionDetail({
  session,
  onBack,
}: {
  session: Session;
  onBack: () => void;
}) {
  const [activeTab, setActiveTab] = React.useState<DetailTab>("chat");

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex shrink-0 items-center gap-3 border-b px-4 py-3">
        <Button variant="ghost" size="icon-sm" onClick={onBack}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-semibold">{session.title}</h2>
        </div>
        {session.harness && (
          <span className="shrink-0 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
            {session.harness}
          </span>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex shrink-0 border-b px-4">
        {(["chat", "files", "terminal"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-3 py-2 text-sm capitalize transition-colors border-b-2 -mb-px",
              activeTab === tab
                ? "border-foreground font-medium text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {activeTab === "chat" && <ChatTab sessionId={session.id} />}
        {activeTab === "files" && (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            Files — Coming Soon
          </div>
        )}
        {activeTab === "terminal" && (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            Terminal — Coming Soon
          </div>
        )}
      </div>
    </div>
  );
}

// ── Chat Tab ────────────────────────────────────────────────────────

function ChatTab({ sessionId }: { sessionId: string }) {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [hasMore, setHasMore] = React.useState(false);
  const [nextCursor, setNextCursor] = React.useState<string | null>(null);
  const [loadingMore, setLoadingMore] = React.useState(false);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  const fetchMessages = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await sessionsApi.getMessages(sessionId, {
        limit: 50,
        order: "asc",
      });
      setMessages(data.messages);
      setHasMore(data.pagination.has_more);
      setNextCursor(data.pagination.next_cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load messages");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  React.useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  React.useEffect(() => {
    if (!loading) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const handleLoadMore = async () => {
    if (!nextCursor) return;
    setLoadingMore(true);
    try {
      const data = await sessionsApi.getMessages(sessionId, {
        cursor: nextCursor,
        limit: 50,
        order: "asc",
      });
      setMessages((prev) => [...prev, ...data.messages]);
      setHasMore(data.pagination.has_more);
      setNextCursor(data.pagination.next_cursor);
    } catch {
      // ignore
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (!content) return;
    setSending(true);
    try {
      const msg = await sessionsApi.sendMessage(sessionId, content);
      setMessages((prev) => [...prev, msg]);
      setInput("");
    } catch {
      // ignore send error for now
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Messages */}
      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-2 p-4">
          {hasMore && (
            <div className="flex justify-center pb-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore && <Loader2 className="size-3.5 animate-spin" />}
                Load older messages
              </Button>
            </div>
          )}

          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <MessageSquare className="size-10 opacity-50" />
              <p className="mt-2 text-sm">No messages yet</p>
            </div>
          )}

          {messages.map((msg) =>
            msg.type === "event" ? (
              <div
                key={msg.id}
                className="mx-auto max-w-lg rounded-md bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground"
              >
                {msg.actor && (
                  <span className="font-medium">{msg.actor}</span>
                )}{" "}
                {msg.action}{" "}
                {msg.target && (
                  <span className="font-mono text-foreground/70">{msg.target}</span>
                )}
                {msg.detail && (
                  <span className="ml-1 text-muted-foreground/70">{msg.detail}</span>
                )}
              </div>
            ) : (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col gap-1 rounded-lg px-3 py-2 max-w-[85%]",
                  msg.role === "user"
                    ? "self-end bg-primary text-primary-foreground"
                    : "self-start bg-muted",
                )}
              >
                <span className="text-xs font-medium opacity-70">
                  {msg.role ?? "unknown"}
                </span>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            ),
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="flex shrink-0 items-center gap-2 border-t px-4 py-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
          disabled={sending}
        />
        <Button type="submit" size="sm" disabled={sending || !input.trim()}>
          {sending ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Send className="size-3.5" />
          )}
        </Button>
      </form>
    </div>
  );
}

// ── Main Sessions View ──────────────────────────────────────────────

export function SessionsView() {
  const [activePath, setActivePath] = React.useState("/");
  const [selectedSession, setSelectedSession] = React.useState<Session | null>(
    null,
  );

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Left: Directory Tree */}
      <div className="flex w-64 shrink-0 flex-col overflow-hidden border-r">
        <div className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <Folder className="size-5" />
          <span className="font-medium">Explorer</span>
        </div>
        <ScrollArea className="min-h-0 flex-1">
          <DirectoryTree activePath={activePath} onSelect={(p) => {
            setActivePath(p);
            setSelectedSession(null);
          }} />
        </ScrollArea>
      </div>

      {/* Right: Session list or Session detail */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {selectedSession ? (
          <SessionDetail
            session={selectedSession}
            onBack={() => setSelectedSession(null)}
          />
        ) : (
          <>
            <div className="flex h-14 shrink-0 items-center border-b px-4">
              <Breadcrumbs path={activePath} onNavigate={(p) => {
                setActivePath(p);
                setSelectedSession(null);
              }} />
            </div>
            <ScrollArea className="min-h-0 flex-1">
              <SessionList
                path={activePath}
                onSelectSession={setSelectedSession}
              />
            </ScrollArea>
          </>
        )}
      </div>
    </div>
  );
}
