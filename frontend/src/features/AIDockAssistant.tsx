import React, { useState } from 'react';
import { MessageSquare, X, ChevronUp, Send, Sparkles, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const AIDockAssistant: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);

    return (
        <div className="fixed bottom-6 right-6 z-50">
            <AnimatePresence>
                {!isOpen && (
                    <motion.button
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        onClick={() => setIsOpen(true)}
                        className="w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform"
                    >
                        <Sparkles className="w-6 h-6" />
                    </motion.button>
                )}

                {isOpen && (
                    <motion.div
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: 100, opacity: 0 }}
                        className={`w-96 bg-card border shadow-2xl rounded-2xl flex flex-col overflow-hidden ${isMinimized ? 'h-14' : 'h-[500px]'}`}
                    >
                        {/* Header */}
                        <div className="p-4 bg-muted/50 border-b flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-primary" />
                                <span className="font-bold text-sm">QueryBridge AI</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => setIsMinimized(!isMinimized)} className="p-1 hover:bg-accent rounded">
                                    <ChevronUp className={`w-4 h-4 transition-transform ${isMinimized ? 'rotate-180' : ''}`} />
                                </button>
                                <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-accent rounded">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        {!isMinimized && (
                            <>
                                {/* Messages */}
                                <div className="flex-1 p-4 space-y-4 overflow-y-auto">
                                    <div className="bg-muted p-3 rounded-2xl rounded-tl-none text-sm max-w-[85%]">
                                        Hello! I'm your enterprise analyst. I can help you query data, certify metrics, or analyze schema drifts.
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {['Analyze Drift', 'Certify Revenue KPI', 'List Tables'].map(tag => (
                                            <button key={tag} className="text-[10px] font-bold px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full hover:bg-primary/20">
                                                {tag}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Input */}
                                <div className="p-4 border-t bg-background">
                                    <div className="relative">
                                        <input 
                                            className="w-full bg-muted border-none rounded-xl py-3 pl-4 pr-12 text-sm focus:ring-1 focus:ring-primary"
                                            placeholder="Ask anything..."
                                        />
                                        <button className="absolute right-2 top-1.5 p-2 bg-primary text-primary-foreground rounded-lg">
                                            <Send className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
