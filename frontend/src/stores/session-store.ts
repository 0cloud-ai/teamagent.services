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
