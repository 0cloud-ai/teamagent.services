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
      // API may return doc-format { name, total } or fs-format { name, type, size }
      // Normalize: keep only directories, ensure total exists
      const children = (data.children ?? [])
        .filter((c: Record<string, unknown>) => !("type" in c) || c.type === "directory")
        .map((c: Record<string, unknown>) => ({
          name: c.name as string,
          total: (c.total as ChildStats["total"]) ?? { directories: 0, sessions: 0, messages: 0 },
        }));
      set({ children });
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
