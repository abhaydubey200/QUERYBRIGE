import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Play, Plus, Brain, Database, Trash } from 'lucide-react';

interface Cell {
    id: string;
    type: 'sql' | 'ai' | 'python';
    content: string;
    output?: any;
    isExecuting?: boolean;
}

export const NotebookPage: React.FC = () => {
    const [cells, setCells] = useState<Cell[]>([
        { id: '1', type: 'sql', content: 'SELECT * FROM users LIMIT 10' }
    ]);

    const addCell = (type: 'sql' | 'ai' | 'python') => {
        setCells([...cells, { id: Math.random().toString(), type, content: '' }]);
    };

    const runCell = (id: string) => {
        setCells(cells.map(c => c.id === id ? { ...c, isExecuting: true } : c));
        // Mock execution
        setTimeout(() => {
            setCells(cells.map(c => c.id === id ? { 
                ...c, 
                isExecuting: false, 
                output: "Execution successful. [Sample Results Streamed]" 
            } : c));
        }, 1500);
    };

    return (
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold">Analytics Notebook</h1>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => addCell('sql')}>
                        <Plus className="w-4 h-4 mr-2" /> SQL Cell
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => addCell('ai')}>
                        <Plus className="w-4 h-4 mr-2" /> AI Cell
                    </Button>
                </div>
            </div>

            <div className="space-y-4">
                {cells.map((cell) => (
                    <Card key={cell.id} className="border-l-4 border-l-blue-500">
                        <CardHeader className="py-2 px-4 flex flex-row items-center justify-between bg-muted/50">
                            <div className="flex items-center gap-2">
                                {cell.type === 'sql' ? <Database className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
                                <span className="text-xs font-bold uppercase tracking-wider">{cell.type} Cell</span>
                            </div>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                                <Trash className="w-4 h-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="relative">
                                <Textarea 
                                    className="min-h-[100px] border-none focus-visible:ring-0 font-mono text-sm p-4 bg-black/5"
                                    value={cell.content}
                                    onChange={(e) => setCells(cells.map(c => c.id === cell.id ? { ...c, content: e.target.value } : c))}
                                    placeholder={cell.type === 'sql' ? "Enter SQL query..." : "Ask the AI analyst..."}
                                />
                                <Button 
                                    size="icon" 
                                    className="absolute bottom-2 right-2 rounded-full w-8 h-8"
                                    onClick={() => runCell(cell.id)}
                                    disabled={cell.isExecuting}
                                >
                                    <Play className="w-4 h-4" />
                                </Button>
                            </div>
                            {cell.output && (
                                <div className="p-4 border-t bg-muted/20 font-mono text-xs whitespace-pre-wrap">
                                    {cell.output}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
};
