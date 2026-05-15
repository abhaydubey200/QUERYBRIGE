import React, { useState } from 'react';
import { useNotebookStore, NotebookCell } from '@/store/notebookStore';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Plus, Trash2, ChevronUp, ChevronDown, Save, Terminal, Database, FileText, BarChart3 } from 'lucide-react';
import Editor from "@monaco-editor/react";
import { cn } from "@/lib/utils";

const NotebooksPage = () => {
  const { cells, addCell, updateCell, removeCell, moveCell, isExecuting, setExecuting } = useNotebookStore();
  const [activeNotebookName, setActiveNotebookName] = useState("Untitled Analysis");

  const executeCell = async (cell: NotebookCell) => {
    updateCell(cell.id, { status: 'running' });
    setExecuting(true);
    const start = Date.now();
    
    try {
      // Real API call to the backend notebook runtime
      const response = await fetch(`/api/v1/notebooks/execute/default?cell_id=${cell.id}&code=${encodeURIComponent(cell.content)}`, {
        method: 'POST'
      });
      const result = await response.json();
      
      updateCell(cell.id, { 
        status: result.status === 'success' ? 'success' : 'error',
        output: result.output || result.error,
        executionTime: Date.now() - start
      });
    } catch (error) {
      updateCell(cell.id, { 
        status: 'error',
        output: String(error),
        executionTime: Date.now() - start
      });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#050505] text-gray-300 overflow-hidden">
      {/* Toolbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Terminal className="text-blue-500" size={20} />
          <input 
            value={activeNotebookName}
            onChange={(e) => setActiveNotebookName(e.target.value)}
            className="bg-transparent text-white font-semibold text-lg outline-none border-b border-transparent focus:border-blue-500/50 transition-colors"
          />
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="bg-white/5 border-white/10 hover:bg-white/10">
            <Save size={16} className="mr-2" /> Save
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20">
            <Play size={16} className="mr-2" /> Run All
          </Button>
        </div>
      </header>

      {/* Canvas */}
      <main className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto w-full space-y-6 pb-32 custom-scrollbar">
        {cells.map((cell, index) => (
          <div key={cell.id} className="group relative">
            <Card className={cn(
              "bg-[#0a0a0a] border-white/5 overflow-hidden transition-all duration-300",
              cell.status === 'running' && "ring-1 ring-blue-500/50",
              cell.status === 'error' && "ring-1 ring-red-500/30"
            )}>
              {/* Cell Controls */}
              <div className="absolute -left-12 top-0 flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="icon" onClick={() => moveCell(cell.id, 'up')} disabled={index === 0}>
                  <ChevronUp size={16} />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => moveCell(cell.id, 'down')} disabled={index === cells.length - 1}>
                  <ChevronDown size={16} />
                </Button>
                <Button variant="ghost" size="icon" className="text-red-500/70 hover:text-red-500" onClick={() => removeCell(cell.id)}>
                  <Trash2 size={16} />
                </Button>
              </div>

              {/* Cell Header */}
              <div className="px-4 py-2 bg-white/5 flex items-center justify-between border-b border-white/5">
                <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-gray-500">
                  {cell.type === 'sql' && <Database size={14} className="text-amber-500" />}
                  {cell.type === 'python' && <Terminal size={14} className="text-blue-500" />}
                  {cell.type === 'markdown' && <FileText size={14} className="text-emerald-500" />}
                  {cell.type === 'chart' && <BarChart3 size={14} className="text-purple-500" />}
                  <span>{cell.type} Cell</span>
                </div>
                <div className="flex items-center gap-3">
                  {cell.executionTime && (
                    <span className="text-[10px] text-gray-600 font-mono">{cell.executionTime}ms</span>
                  )}
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 w-7 p-0 hover:bg-blue-500/10 hover:text-blue-500"
                    onClick={() => executeCell(cell)}
                    disabled={isExecuting}
                  >
                    <Play size={14} />
                  </Button>
                </div>
              </div>

              {/* Editor */}
              <div className="min-h-[100px] bg-black/20">
                {cell.type === 'markdown' ? (
                  <textarea
                    value={cell.content}
                    onChange={(e) => updateCell(cell.id, { content: e.target.value })}
                    className="w-full bg-transparent p-4 outline-none resize-none font-sans text-gray-300 min-h-[100px]"
                    placeholder="Enter markdown..."
                  />
                ) : (
                  <Editor
                    height="150px"
                    theme="vs-dark"
                    language={cell.type === 'sql' ? 'sql' : 'python'}
                    value={cell.content}
                    onChange={(val) => updateCell(cell.id, { content: val || '' })}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 13,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      padding: { top: 12, bottom: 12 }
                    }}
                  />
                )}
              </div>

              {/* Output */}
              {cell.output && (
                <div className={cn(
                  "p-4 border-t border-white/5 font-mono text-xs",
                  cell.status === 'error' ? "bg-red-500/5 text-red-400" : "bg-black/40 text-gray-400"
                )}>
                  <pre className="whitespace-pre-wrap">{cell.output}</pre>
                </div>
              )}
            </Card>
          </div>
        ))}

        {/* Add Cell Buttons */}
        <div className="flex justify-center gap-4 py-8">
          <Button variant="outline" className="border-white/10 hover:bg-amber-500/10 hover:border-amber-500/30" onClick={() => addCell('sql')}>
            <Database size={16} className="mr-2 text-amber-500" /> SQL
          </Button>
          <Button variant="outline" className="border-white/10 hover:bg-blue-500/10 hover:border-blue-500/30" onClick={() => addCell('python')}>
            <Terminal size={16} className="mr-2 text-blue-500" /> Python
          </Button>
          <Button variant="outline" className="border-white/10 hover:bg-emerald-500/10 hover:border-emerald-500/30" onClick={() => addCell('markdown')}>
            <FileText size={16} className="mr-2 text-emerald-500" /> Markdown
          </Button>
        </div>
      </main>
    </div>
  );
};

export default NotebooksPage;
