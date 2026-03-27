"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Loader2, ChevronDown, Settings2 } from "lucide-react";
import { harnessApi, providersApi } from "@/lib/api";
import type { Engine, HarnessResponse, Provider, Binding } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const ROLE_COLORS: Record<string, string> = {
  default: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  reasoning: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
  fast: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  local: "bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-300",
};

function roleColor(role: string) {
  return ROLE_COLORS[role] ?? "bg-secondary text-secondary-foreground";
}

const BINDING_ROLES = ["default", "reasoning", "fast", "local"];

export function HarnessView() {
  const [harness, setHarness] = useState<HarnessResponse | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addBindingEngine, setAddBindingEngine] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [h, p] = await Promise.all([
        harnessApi.get(),
        providersApi.list(),
      ]);
      setHarness(h);
      setProviders(p.providers);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load harness");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSetDefault(engineId: string) {
    try {
      const result = await harnessApi.setDefault(engineId);
      setHarness(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to set default engine");
    }
  }

  async function handleDeleteBinding(engineId: string, providerId: string) {
    try {
      await harnessApi.deleteBinding(engineId, providerId);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete binding");
    }
  }

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!harness) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        No harness configuration found.
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">Harness</h1>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Default engine:</span>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={<Button variant="outline" size="sm" />}
              >
                <Settings2 data-icon="inline-start" className="size-3.5" />
                {harness.default}
                <ChevronDown data-icon="inline-end" className="size-3" />
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {harness.engines.map((engine) => (
                  <DropdownMenuItem
                    key={engine.id}
                    onClick={() => handleSetDefault(engine.id)}
                  >
                    {engine.name}
                    {engine.id === harness.default && (
                      <Badge variant="secondary" className="ml-auto text-[10px]">
                        current
                      </Badge>
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {error && (
        <div className="mx-6 mt-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Engines */}
      <ScrollArea className="flex-1">
        <div className="space-y-6 p-6">
          {harness.engines.map((engine) => (
            <EngineCard
              key={engine.id}
              engine={engine}
              isDefault={engine.id === harness.default}
              onDeleteBinding={(providerId) =>
                handleDeleteBinding(engine.id, providerId)
              }
              onAddBinding={() => setAddBindingEngine(engine.id)}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Add Binding Dialog */}
      <AddBindingDialog
        engineId={addBindingEngine}
        providers={providers}
        onClose={() => setAddBindingEngine(null)}
        onSuccess={load}
      />
    </div>
  );
}

// ── Engine Card ──────────────────────────────────────────────────────

function EngineCard({
  engine,
  isDefault,
  onDeleteBinding,
  onAddBinding,
}: {
  engine: Engine;
  isDefault: boolean;
  onDeleteBinding: (providerId: string) => void;
  onAddBinding: () => void;
}) {
  return (
    <div className="rounded-lg border border-border">
      {/* Engine header */}
      <div className="flex items-start justify-between p-4 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              {engine.name}
            </h3>
            {isDefault && <Badge variant="default">default</Badge>}
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {engine.description}
          </p>
          {engine.supported_vendors.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {engine.supported_vendors.map((v) => (
                <Badge key={v} variant="outline" className="text-[10px]">
                  {v}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onAddBinding}>
          <Plus data-icon="inline-start" className="size-3.5" />
          Add Binding
        </Button>
      </div>

      {/* Bindings table */}
      {engine.bindings.length > 0 && (
        <div className="border-t border-border">
          <div className="grid grid-cols-[1fr_1fr_auto_auto] gap-x-4 px-4 py-2 text-xs font-medium text-muted-foreground">
            <span>Vendor</span>
            <span>Model</span>
            <span>Role</span>
            <span />
          </div>
          {engine.bindings.map((binding) => (
            <BindingRow
              key={binding.provider_id}
              binding={binding}
              onDelete={() => onDeleteBinding(binding.provider_id)}
            />
          ))}
        </div>
      )}

      {engine.bindings.length === 0 && (
        <div className="border-t border-border px-4 py-6 text-center text-xs text-muted-foreground">
          No bindings configured for this engine.
        </div>
      )}
    </div>
  );
}

function BindingRow({
  binding,
  onDelete,
}: {
  binding: Binding;
  onDelete: () => void;
}) {
  return (
    <div className="grid grid-cols-[1fr_1fr_auto_auto] items-center gap-x-4 border-t border-border/50 px-4 py-2 hover:bg-muted/30">
      <span className="truncate text-sm text-foreground">{binding.vendor}</span>
      <span className="truncate text-sm text-muted-foreground">
        {binding.model}
      </span>
      <span
        className={cn(
          "inline-flex h-5 items-center rounded-full px-2 text-[10px] font-medium",
          roleColor(binding.role),
        )}
      >
        {binding.role}
      </span>
      <Button
        variant="ghost"
        size="icon-xs"
        onClick={onDelete}
        aria-label="Delete binding"
      >
        <Trash2 className="size-3 text-destructive" />
      </Button>
    </div>
  );
}

// ── Add Binding Dialog ───────────────────────────────────────────────

function AddBindingDialog({
  engineId,
  providers,
  onClose,
  onSuccess,
}: {
  engineId: string | null;
  providers: Provider[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [providerId, setProviderId] = useState("");
  const [role, setRole] = useState("default");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setProviderId("");
    setRole("default");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!engineId || !providerId) return;
    setSubmitting(true);
    setError(null);
    try {
      await harnessApi.addBinding(engineId, providerId, role);
      reset();
      onClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add binding");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog
      open={!!engineId}
      onOpenChange={(v) => {
        if (!v) {
          reset();
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Binding</DialogTitle>
          <DialogDescription>
            Bind a provider to this engine.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <select
            value={providerId}
            onChange={(e) => setProviderId(e.target.value)}
            required
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <option value="">Select provider...</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.vendor} / {p.model}
              </option>
            ))}
          </select>

          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            {BINDING_ROLES.map((r) => (
              <option key={r} value={r}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </option>
            ))}
          </select>

          {error && <p className="text-xs text-destructive">{error}</p>}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset();
                onClose();
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !providerId}>
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
