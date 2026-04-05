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
