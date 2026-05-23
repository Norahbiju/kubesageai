import { create } from "zustand";
import type { Cluster } from "@/lib/types";

interface AppState {
  selectedCluster?: Cluster;
  setSelectedCluster: (cluster?: Cluster) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedCluster: undefined,
  setSelectedCluster: (cluster) => set({ selectedCluster: cluster })
}));
