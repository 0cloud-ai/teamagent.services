"use client";

import { useCallback, useEffect, useState } from "react";
import { User, Globe, Plus, Trash2, Radio, Loader2 } from "lucide-react";
import { membersApi } from "@/lib/api";
import type { Member, PingResult } from "@/lib/types";
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

export function MembersView() {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Member | null>(null);
  const [pingResults, setPingResults] = useState<Record<string, PingResult>>({});
  const [pinging, setPinging] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await membersApi.list();
      setMembers(data.members);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(member: Member) {
    try {
      await membersApi.remove(member.id);
      setDeleteTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete member");
    }
  }

  async function handlePing(memberId: string) {
    setPinging((p) => ({ ...p, [memberId]: true }));
    try {
      const result = await membersApi.ping(memberId);
      setPingResults((r) => ({ ...r, [memberId]: result }));
    } catch {
      setPingResults((r) => ({
        ...r,
        [memberId]: { status: "error", error: "Ping failed" },
      }));
    } finally {
      setPinging((p) => ({ ...p, [memberId]: false }));
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h1 className="text-lg font-semibold text-foreground">Members</h1>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus data-icon="inline-start" className="size-4" />
          Add Member
        </Button>
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* List */}
      <ScrollArea className="flex-1">
        <div className="divide-y divide-border">
          {members.length === 0 && (
            <div className="px-6 py-12 text-center text-sm text-muted-foreground">
              No members yet. Add one to get started.
            </div>
          )}
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center gap-4 px-6 py-3 hover:bg-muted/30"
            >
              {/* Icon */}
              <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted">
                {member.type === "user" ? (
                  <User className="size-4 text-muted-foreground" />
                ) : (
                  <Globe className="size-4 text-muted-foreground" />
                )}
              </div>

              {/* Name + info */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {member.name}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {member.email ?? member.service_url ?? member.id}
                </p>
              </div>

              {/* Type badge */}
              <Badge variant="secondary">{member.type}</Badge>

              {/* Role / Status */}
              {member.role && (
                <Badge variant="outline">{member.role}</Badge>
              )}
              {member.status && (
                <Badge
                  variant={member.status === "active" ? "default" : "secondary"}
                >
                  {member.status}
                </Badge>
              )}

              {/* Joined */}
              <span className="shrink-0 text-xs text-muted-foreground">
                {formatDate(member.joined_at)}
              </span>

              {/* Ping result */}
              {pingResults[member.id] && (
                <span
                  className={cn(
                    "shrink-0 text-xs",
                    pingResults[member.id].status === "ok"
                      ? "text-emerald-600"
                      : "text-destructive",
                  )}
                >
                  {pingResults[member.id].status === "ok"
                    ? `${pingResults[member.id].latency_ms}ms`
                    : "err"}
                </span>
              )}

              {/* Actions */}
              <div className="flex shrink-0 items-center gap-1">
                {member.type === "service" && (
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => handlePing(member.id)}
                    disabled={pinging[member.id]}
                    aria-label="Ping"
                  >
                    {pinging[member.id] ? (
                      <Loader2 className="size-3 animate-spin" />
                    ) : (
                      <Radio className="size-3" />
                    )}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={() => setDeleteTarget(member)}
                  aria-label="Delete"
                >
                  <Trash2 className="size-3 text-destructive" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Add Dialog */}
      <AddMemberDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={load}
      />

      {/* Delete Confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Member</DialogTitle>
            <DialogDescription>
              Remove <strong>{deleteTarget?.name}</strong> from this workspace?
              This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteTarget && handleDelete(deleteTarget)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Add Member Dialog ────────────────────────────────────────────────

function AddMemberDialog({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSuccess: () => void;
}) {
  const [type, setType] = useState<"user" | "service">("user");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");
  const [serviceUrl, setServiceUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setType("user");
    setName("");
    setEmail("");
    setRole("member");
    setServiceUrl("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await membersApi.add({
        type,
        name,
        ...(type === "user" ? { email, role } : { service_url: serviceUrl }),
      });
      reset();
      onOpenChange(false);
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Member</DialogTitle>
          <DialogDescription>
            Add a user or service member to this workspace.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {/* Type select */}
          <div className="flex gap-2">
            <Button
              type="button"
              variant={type === "user" ? "default" : "outline"}
              size="sm"
              onClick={() => setType("user")}
            >
              <User data-icon="inline-start" className="size-3.5" />
              User
            </Button>
            <Button
              type="button"
              variant={type === "service" ? "default" : "outline"}
              size="sm"
              onClick={() => setType("service")}
            >
              <Globe data-icon="inline-start" className="size-3.5" />
              Service
            </Button>
          </div>

          <Input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          {type === "user" ? (
            <>
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
            </>
          ) : (
            <Input
              type="url"
              placeholder="Service URL"
              value={serviceUrl}
              onChange={(e) => setServiceUrl(e.target.value)}
              required
            />
          )}

          {error && (
            <p className="text-xs text-destructive">{error}</p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset();
                onOpenChange(false);
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                "Add"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
