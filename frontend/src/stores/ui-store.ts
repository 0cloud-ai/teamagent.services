import { create } from "zustand";

type ActiveTab = "files" | "datas" | "services";

type UIState = {
  activeTab: ActiveTab;
  isDetailPanelOpen: boolean;
  setActiveTab: (tab: ActiveTab) => void;
  toggleDetailPanel: () => void;
  setDetailPanelOpen: (open: boolean) => void;
};

export const useUIStore = create<UIState>((set) => ({
  activeTab: "files",
  isDetailPanelOpen: true,

  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleDetailPanel: () => set((s) => ({ isDetailPanelOpen: !s.isDetailPanelOpen })),
  setDetailPanelOpen: (open) => set({ isDetailPanelOpen: open }),
}));
