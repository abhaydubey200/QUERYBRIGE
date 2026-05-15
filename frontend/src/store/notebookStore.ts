import { create } from 'zustand';

export interface NotebookCell {
  id: string;
  type: 'sql' | 'python' | 'markdown' | 'chart';
  content: string;
  output?: any;
  status: 'idle' | 'running' | 'success' | 'error';
  executionTime?: number;
}

interface NotebookState {
  cells: NotebookCell[];
  activeCellId: string | null;
  isExecuting: boolean;
  addCell: (type: NotebookCell['type']) => void;
  updateCell: (id: string, updates: Partial<NotebookCell>) => void;
  removeCell: (id: string) => void;
  moveCell: (id: string, direction: 'up' | 'down') => void;
  setExecuting: (isExecuting: boolean) => void;
}

export const useNotebookStore = create<NotebookState>((set) => ({
  cells: [
    { id: '1', type: 'markdown', content: '# Welcome to QueryBridge Notebooks\nStart by adding a SQL or Python cell below.', status: 'idle' }
  ],
  activeCellId: null,
  isExecuting: false,
  addCell: (type) => set((state) => ({
    cells: [...state.cells, { id: Math.random().toString(36).substr(2, 9), type, content: '', status: 'idle' }]
  })),
  updateCell: (id, updates) => set((state) => ({
    cells: state.cells.map(cell => cell.id === id ? { ...cell, ...updates } : cell)
  })),
  removeCell: (id) => set((state) => ({
    cells: state.cells.filter(cell => cell.id !== id)
  })),
  moveCell: (id, direction) => set((state) => {
    const index = state.cells.findIndex(c => c.id === id);
    if (index === -1) return state;
    const newCells = [...state.cells];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newCells.length) return state;
    [newCells[index], newCells[targetIndex]] = [newCells[targetIndex], newCells[index]];
    return { cells: newCells };
  }),
  setExecuting: (isExecuting) => set({ isExecuting })
}));
