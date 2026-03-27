"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  RotateCcw,
  Tag,
  Loader2,
  MessageSquare,
  X,
} from "lucide-react";
import { serviceInboxApi } from "@/lib/api";
import type { InboxConversation, InboxConversationDetail } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

type StatusFilter = "all" | "open" | "escalated" | "closed";

const STATUS_CONFIG: Record<
  string,
  { color: string; dotColor: string }
> = {
  open: {
    color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
    dotColor: "bg-emerald-500",
  },
  escalated: {
    color: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
    dotColor: "bg-amber-500",
  },
  closed: {
    color: "bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400",
    dotColor: "bg-gray-400",
  },
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function ServiceInboxView() {
  const [conversations, setConversations] = useState<InboxConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<StatusFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await serviceInboxApi.list(
        filter === "all" ? {} : { status: filter },
      );
      setConversations(data.conversations);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load inbox");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  // If a conversation is selected, show detail view
  if (selectedId) {
    return (
      <ConversationDetailView
        conversationId={selectedId}
        onBack={() => {
          setSelectedId(null);
          load();
        }}
      />
    );
  }

  const tabs: { id: StatusFilter; label: string }[] = [
    { id: "all", label: "All" },
    { id: "open", label: "Open" },
    { id: "escalated", label: "Escalated" },
    { id: "closed", label: "Closed" },
  ];

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-lg font-semibold text-foreground">Service Inbox</h1>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 border-b border-border px-6 py-2">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={filter === tab.id ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setFilter(tab.id)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <ScrollArea className="flex-1">
          <div className="divide-y divide-border">
            {conversations.length === 0 && (
              <div className="px-6 py-12 text-center text-sm text-muted-foreground">
                No conversations found.
              </div>
            )}
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedId(conv.id)}
                className="flex w-full items-center gap-4 px-6 py-3 text-left transition-colors hover:bg-muted/30"
              >
                {/* Status dot */}
                <span
                  className={cn(
                    "size-2.5 shrink-0 rounded-full",
                    STATUS_CONFIG[conv.status]?.dotColor ?? "bg-gray-400",
                  )}
                />

                {/* Title + consumer */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">
                    {conv.title}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {conv.consumer.name}
                  </p>
                </div>

                {/* Status badge */}
                <span
                  className={cn(
                    "inline-flex h-5 shrink-0 items-center rounded-full px-2 text-[10px] font-medium",
                    STATUS_CONFIG[conv.status]?.color ?? "bg-secondary text-secondary-foreground",
                  )}
                >
                  {conv.status}
                </span>

                {/* Labels */}
                {conv.labels.length > 0 && (
                  <div className="hidden shrink-0 items-center gap-1 sm:flex">
                    {conv.labels.slice(0, 2).map((label) => (
                      <Badge
                        key={label}
                        variant="outline"
                        className="text-[10px]"
                      >
                        {label}
                      </Badge>
                    ))}
                    {conv.labels.length > 2 && (
                      <span className="text-xs text-muted-foreground">
                        +{conv.labels.length - 2}
                      </span>
                    )}
                  </div>
                )}

                {/* Message count */}
                <div className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
                  <MessageSquare className="size-3" />
                  {conv.message_count}
                </div>

                {/* Time */}
                <span className="shrink-0 text-xs text-muted-foreground">
                  {relativeTime(conv.updated_at)}
                </span>
              </button>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

// ── Conversation Detail View ─────────────────────────────────────────

function ConversationDetailView({
  conversationId,
  onBack,
}: {
  conversationId: string;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<InboxConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);
  const [labelsOpen, setLabelsOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await serviceInboxApi.getDetail(conversationId);
      setDetail(data);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load conversation");
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAction(
    action: "escalate" | "close" | "reopen",
  ) {
    setActing(true);
    try {
      let result: InboxConversationDetail;
      if (action === "escalate") {
        result = await serviceInboxApi.escalate(conversationId);
      } else if (action === "close") {
        result = await serviceInboxApi.close(conversationId);
      } else {
        result = await serviceInboxApi.reopen(conversationId);
      }
      setDetail(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : `Failed to ${action}`);
    } finally {
      setActing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex flex-1 flex-col">
        <div className="border-b border-border px-6 py-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft data-icon="inline-start" className="size-4" />
            Back
          </Button>
        </div>
        <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
          Conversation not found.
        </div>
      </div>
    );
  }

  const statusConf = STATUS_CONFIG[detail.status];

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border px-6 py-4">
        <Button variant="ghost" size="icon-sm" onClick={onBack}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-semibold text-foreground">
            {detail.title}
          </h2>
          <p className="text-xs text-muted-foreground">
            {detail.consumer.name}
          </p>
        </div>
        <span
          className={cn(
            "inline-flex h-5 items-center rounded-full px-2 text-[10px] font-medium",
            statusConf?.color ?? "bg-secondary text-secondary-foreground",
          )}
        >
          {detail.status}
        </span>
      </div>

      {/* Actions bar */}
      <div className="flex items-center gap-2 border-b border-border px-6 py-2">
        {detail.status === "open" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction("escalate")}
            disabled={acting}
          >
            <AlertTriangle data-icon="inline-start" className="size-3.5" />
            Escalate
          </Button>
        )}
        {detail.status !== "closed" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction("close")}
            disabled={acting}
          >
            <CheckCircle2 data-icon="inline-start" className="size-3.5" />
            Close
          </Button>
        )}
        {detail.status === "closed" && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleAction("reopen")}
            disabled={acting}
          >
            <RotateCcw data-icon="inline-start" className="size-3.5" />
            Reopen
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setLabelsOpen(true)}
        >
          <Tag data-icon="inline-start" className="size-3.5" />
          Labels
          {detail.labels.length > 0 && (
            <Badge variant="secondary" className="ml-1 text-[10px]">
              {detail.labels.length}
            </Badge>
          )}
        </Button>

        {acting && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Messages + sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Messages */}
        <ScrollArea className="flex-1">
          <div className="space-y-3 p-6">
            {detail.messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "rounded-lg p-3",
                  msg.role === "user"
                    ? "bg-muted/50"
                    : "border border-border bg-background",
                )}
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-medium text-foreground">
                    {msg.role === "user" ? "User" : "Assistant"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {relativeTime(msg.created_at)}
                  </span>
                </div>
                <p className="whitespace-pre-wrap text-sm text-foreground">
                  {msg.content}
                </p>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Sidebar: labels + referenced sessions */}
        <div className="hidden w-60 shrink-0 border-l border-border lg:block">
          <ScrollArea className="h-full">
            <div className="p-4">
              {/* Labels */}
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Labels
              </h4>
              {detail.labels.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {detail.labels.map((label) => (
                    <Badge key={label} variant="outline">
                      {label}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No labels</p>
              )}

              {/* Referenced sessions */}
              <h4 className="mb-2 mt-6 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Referenced Sessions
              </h4>
              {detail.referenced_by.length > 0 ? (
                <div className="space-y-1">
                  {detail.referenced_by.map((ref) => (
                    <div
                      key={ref.session_id}
                      className="rounded-md bg-muted/50 px-2 py-1.5 text-xs text-foreground"
                    >
                      {ref.session_title}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">
                  No sessions reference this conversation
                </p>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Edit Labels Dialog */}
      <EditLabelsDialog
        open={labelsOpen}
        onOpenChange={setLabelsOpen}
        conversationId={conversationId}
        currentLabels={detail.labels}
        onSuccess={(updated) => setDetail(updated)}
      />
    </div>
  );
}

// ── Edit Labels Dialog ───────────────────────────────────────────────

function EditLabelsDialog({
  open,
  onOpenChange,
  conversationId,
  currentLabels,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  conversationId: string;
  currentLabels: string[];
  onSuccess: (detail: InboxConversationDetail) => void;
}) {
  const [labels, setLabels] = useState<string[]>(currentLabels);
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync when dialog opens
  useEffect(() => {
    if (open) {
      setLabels(currentLabels);
      setInput("");
      setError(null);
    }
  }, [open, currentLabels]);

  function addLabel() {
    const trimmed = input.trim();
    if (trimmed && !labels.includes(trimmed)) {
      setLabels([...labels, trimmed]);
    }
    setInput("");
  }

  function removeLabel(label: string) {
    setLabels(labels.filter((l) => l !== label));
  }

  async function handleSave() {
    setSubmitting(true);
    setError(null);
    try {
      const result = await serviceInboxApi.updateLabels(conversationId, labels);
      onSuccess(result);
      onOpenChange(false);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to update labels");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Edit Labels</DialogTitle>
          <DialogDescription>
            Add or remove labels for this conversation.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          {/* Input to add */}
          <div className="flex gap-2">
            <Input
              placeholder="Add label..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addLabel();
                }
              }}
            />
            <Button type="button" variant="outline" size="default" onClick={addLabel}>
              Add
            </Button>
          </div>

          {/* Current labels */}
          <div className="flex flex-wrap gap-1">
            {labels.map((label) => (
              <Badge key={label} variant="secondary" className="gap-1">
                {label}
                <button
                  onClick={() => removeLabel(label)}
                  className="ml-0.5 rounded-full hover:bg-foreground/10"
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
            {labels.length === 0 && (
              <p className="text-xs text-muted-foreground">No labels</p>
            )}
          </div>

          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={submitting}>
            {submitting ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              "Save"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
