import { create } from 'zustand';

interface ConnectionState {
  connections: any[];
  activeConnection: any | null;
  loading: boolean;
  error: string | null;
  setConnections: (connections: any[]) => void;
  setActiveConnection: (connection: any) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateConnectionStatus: (id: string, status: string, latency: string) => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  connections: [],
  activeConnection: null,
  loading: false,
  error: null,
  setConnections: (connections) => set({ connections }),
  setActiveConnection: (activeConnection) => set({ activeConnection }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  updateConnectionStatus: (id, status, latency) => set((state) => ({
    connections: state.connections.map(c => 
      c.id === id ? { ...c, status, latency } : c
    )
  })),
}));
