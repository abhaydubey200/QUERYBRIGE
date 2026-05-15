import React, { useState, useEffect } from 'react';
import { Search, Command, Database, Brain, Layout, Settings } from 'lucide-react';
import { useWorkspaceStore } from '@/store/workspaceStore';

export const CommandPalette: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setIsOpen((prev) => !prev);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    if (!isOpen) return null;

    const actions = [
        { name: 'New Notebook', icon: <Database className="w-4 h-4" />, shortcut: 'N' },
        { name: 'AI Analyst', icon: <Brain className="w-4 h-4" />, shortcut: 'A' },
        { name: 'Dashboard Studio', icon: <Layout className="w-4 h-4" />, shortcut: 'D' },
        { name: 'Settings', icon: <Settings className="w-4 h-4" />, shortcut: ',' },
    ];

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/40 backdrop-blur-sm">
            <div className="w-full max-w-2xl bg-card border shadow-2xl rounded-xl overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex items-center p-4 border-b bg-muted/30">
                    <Search className="w-5 h-5 text-muted-foreground mr-3" />
                    <input 
                        autoFocus
                        className="flex-1 bg-transparent border-none outline-none text-lg"
                        placeholder="Search metrics, dashboards, or commands (Ctrl + K)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded text-[10px] font-bold text-muted-foreground">
                        <Command className="w-3 h-3" /> K
                    </div>
                </div>
                <div className="p-2">
                    <div className="text-[10px] font-bold text-muted-foreground px-3 py-2 uppercase tracking-widest">Quick Actions</div>
                    {actions.map((action) => (
                        <div key={action.name} className="flex items-center justify-between p-3 rounded-lg hover:bg-accent cursor-pointer group">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-muted rounded group-hover:bg-background">
                                    {action.icon}
                                </div>
                                <span className="font-medium">{action.name}</span>
                            </div>
                            <span className="text-[10px] font-bold text-muted-foreground bg-muted px-2 py-1 rounded">Alt + {action.shortcut}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
