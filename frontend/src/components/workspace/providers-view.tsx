"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Radio, Loader2 } from "lucide-react";
import { providersApi } from "@/lib/api";
import type { Provider, PingResult } from "@/lib/types";
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

const VENDOR_COLORS: Record<string, string> = {
  openai: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  anthropic: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  google: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  mistral: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
  meta: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300",
  local: "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-300",
};

function vendorColor(vendor: string) {
  return VENDOR_COLORS[vendor.toLowerCase()] ?? "bg-secondary text-secondary-foreground";
}

const VENDORS = ["openai", "anthropic", "google", "mistral", "meta", "local"];

export function ProvidersView() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Provider | null>(null);
  const [pingResults, setPingResults] = useState<Record<string, PingResult>>({});
  const [pinging, setPinging] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await providersApi.list();
      setProviders(data.providers);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load providers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(provider: Provider) {
    try {
      await providersApi.remove(provider.id);
      setDeleteTarget(null);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete provider");
    }
  }

  async function handlePing(providerId: string) {
    setPinging((p) => ({ ...p, [providerId]: true }));
    try {
      const result = await providersApi.ping(providerId);
      setPingResults((r) => ({ ...r, [providerId]: result }));
    } catch {
      setPingResults((r) => ({
        ...r,
        [providerId]: { status: "error", error: "Ping failed" },
      }));
    } finally {
      setPinging((p) => ({ ...p, [providerId]: false }));
    }
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
        <h1 className="text-lg font-semibold text-foreground">Providers</h1>
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus data-icon="inline-start" className="size-4" />
          Add Provider
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
          {providers.length === 0 && (
            <div className="px-6 py-12 text-center text-sm text-muted-foreground">
              No providers configured. Add one to connect an LLM.
            </div>
          )}
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="flex items-center gap-4 px-6 py-3 hover:bg-muted/30"
            >
              {/* Vendor badge */}
              <span
                className={cn(
                  "inline-flex h-5 shrink-0 items-center rounded-full px-2 text-xs font-medium",
                  vendorColor(provider.vendor),
                )}
              >
                {provider.vendor}
              </span>

              {/* Model */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {provider.model}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {provider.api_base}
                </p>
              </div>

              {/* Status indicator */}
              <div className="flex shrink-0 items-center gap-1.5">
                <span
                  className={cn(
                    "size-2 rounded-full",
                    provider.status === "healthy"
                      ? "bg-emerald-500"
                      : provider.status === "degraded"
                        ? "bg-amber-500"
                        : "bg-gray-400",
                  )}
                />
                <span className="text-xs text-muted-foreground">
                  {provider.status}
                </span>
              </div>

              {/* Used by */}
              {provider.used_by.length > 0 && (
                <div className="hidden shrink-0 items-center gap-1 sm:flex">
                  {provider.used_by.slice(0, 3).map((engine) => (
                    <Badge key={engine} variant="outline" className="text-[10px]">
                      {engine}
                    </Badge>
                  ))}
                  {provider.used_by.length > 3 && (
                    <span className="text-xs text-muted-foreground">
                      +{provider.used_by.length - 3}
                    </span>
                  )}
                </div>
              )}

              {/* Ping result */}
              {pingResults[provider.id] && (
                <span
                  className={cn(
                    "shrink-0 text-xs",
                    pingResults[provider.id].status === "ok"
                      ? "text-emerald-600"
                      : "text-destructive",
                  )}
                >
                  {pingResults[provider.id].status === "ok"
                    ? `${pingResults[provider.id].latency_ms}ms`
                    : "err"}
                </span>
              )}

              {/* Actions */}
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={() => handlePing(provider.id)}
                  disabled={pinging[provider.id]}
                  aria-label="Ping"
                >
                  {pinging[provider.id] ? (
                    <Loader2 className="size-3 animate-spin" />
                  ) : (
                    <Radio className="size-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={() => setDeleteTarget(provider)}
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
      <AddProviderDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onSuccess={load}
      />

      {/* Delete Confirm */}
      <Dialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Provider</DialogTitle>
            <DialogDescription>
              Remove <strong>{deleteTarget?.vendor}/{deleteTarget?.model}</strong>?
              Engines using this provider will lose access.
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

// ── Add Provider Dialog ──────────────────────────────────────────────

function AddProviderDialog({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSuccess: () => void;
}) {
  const [vendor, setVendor] = useState("openai");
  const [model, setModel] = useState("");
  const [apiBase, setApiBase] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setVendor("openai");
    setModel("");
    setApiBase("");
    setApiKey("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await providersApi.create({
        vendor,
        model,
        ...(apiBase ? { api_base: apiBase } : {}),
        ...(apiKey ? { api_key: apiKey } : {}),
      });
      reset();
      onOpenChange(false);
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add provider");
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
          <DialogTitle>Add Provider</DialogTitle>
          <DialogDescription>
            Connect a new LLM provider to this workspace.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <select
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            {VENDORS.map((v) => (
              <option key={v} value={v}>
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </option>
            ))}
          </select>

          <Input
            placeholder="Model (e.g. gpt-4o)"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            required
          />

          <Input
            placeholder="API Base URL (optional)"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
          />

          <Input
            type="password"
            placeholder="API Key (optional)"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />

          {error && <p className="text-xs text-destructive">{error}</p>}

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
