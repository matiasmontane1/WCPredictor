import { create } from 'zustand'

interface AppStore {
  syncJobId: string | null
  setSyncJobId: (id: string | null) => void
}

export const useAppStore = create<AppStore>((set) => ({
  syncJobId: null,
  setSyncJobId: (id) => set({ syncJobId: id }),
}))
