import { create } from 'zustand';

interface WorkspaceState {
  activeQuery: string;
  queryResults: any[];
  isExecuting: boolean;
  connections: any[];
  maxBrowserRows: number;
  setActiveQuery: (query: string) => void;
  setQueryResults: (results: any[]) => void;
  setExecuting: (status: boolean) => void;
  setConnections: (connections: any[]) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  activeQuery: '',
  queryResults: [],
  isExecuting: false,
  connections: [],
  maxBrowserRows: 100000, // Phase 3: Memory Protection
  setActiveQuery: (query) => set({ activeQuery: query }),
  setQueryResults: (results) => {
    // Phase 3: Slice results to prevent browser crash
    const slicedResults = results.slice(0, 100000);
    set({ queryResults: slicedResults });
  },
  setExecuting: (status) => set({ isExecuting: status }),
  setConnections: (connections) => set({ connections }),
}));
