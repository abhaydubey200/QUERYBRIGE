import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Command, Terminal, FileText, Database, Shield } from 'lucide-react';

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      if (e.key === 'Escape') setIsOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const commands = [
    { id: '1', name: 'Search Workspace', icon: Search, shortcut: 'S' },
    { id: '2', name: 'Open Notebook', icon: FileText, shortcut: 'N' },
    { id: '3', name: 'Manage Connections', icon: Database, shortcut: 'C' },
    { id: '4', name: 'System Diagnostics', icon: Terminal, shortcut: 'D' },
    { id: '5', name: 'Security Audit', icon: Shield, shortcut: 'A' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden"
          >
            <div className="flex items-center px-4 py-3 border-b border-slate-700">
              <Search className="w-5 h-5 text-slate-400 mr-3" />
              <input
                autoFocus
                className="flex-1 bg-transparent border-none outline-none text-slate-100 placeholder-slate-500 text-lg"
                placeholder="Type a command or search..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <div className="flex items-center space-x-1 px-2 py-1 bg-slate-800 rounded border border-slate-700">
                <Command className="w-3 h-3 text-slate-400" />
                <span className="text-[10px] text-slate-400 font-medium">K</span>
              </div>
            </div>

            <div className="max-h-[400px] overflow-y-auto p-2">
              <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Suggestions
              </div>
              {commands.map((cmd) => (
                <div
                  key={cmd.id}
                  className="flex items-center justify-between px-3 py-3 rounded-xl hover:bg-slate-800 cursor-pointer transition-colors group"
                >
                  <div className="flex items-center">
                    <div className="p-2 bg-slate-800 rounded-lg mr-3 group-hover:bg-blue-500/20 group-hover:text-blue-400 transition-colors">
                      <cmd.icon className="w-5 h-5" />
                    </div>
                    <span className="text-slate-200 font-medium">{cmd.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-slate-500 font-mono bg-slate-950 px-2 py-1 rounded">Alt + {cmd.shortcut}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 bg-slate-950/50 border-t border-slate-700 flex justify-between items-center text-[10px] text-slate-500">
              <div className="flex space-x-4">
                <span><kbd className="bg-slate-800 px-1.5 py-0.5 rounded mr-1">↑↓</kbd> Navigate</span>
                <span><kbd className="bg-slate-800 px-1.5 py-0.5 rounded mr-1">Enter</kbd> Select</span>
              </div>
              <span>QueryBridge Phase 7 Enterprise</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
