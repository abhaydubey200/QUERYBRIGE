import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Brain, Layout, Save, Sparkles } from 'lucide-react';

export const DashboardStudio: React.FC = () => {
    const [prompt, setPrompt] = useState('');
    const [widgets, setWidgets] = useState<any[]>([]);

    const generateDashboard = () => {
        // AI logic would be called here
        setWidgets([
            { id: '1', title: 'Total Revenue', type: 'kpi', value: '$1.2M' },
            { id: '2', title: 'Revenue by Region', type: 'chart', chartType: 'bar' },
            { id: '3', title: 'Customer Churn Risk', type: 'insight', content: 'Risk increased in EMEA region.' }
        ]);
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center bg-card p-4 rounded-xl border shadow-sm">
                <div className="flex items-center gap-4 flex-1 max-w-2xl">
                    <Sparkles className="w-6 h-6 text-purple-500" />
                    <Input 
                        placeholder="What dashboard do you want to build? (e.g. 'FMCG Sales Overview')" 
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        className="bg-muted/50 border-none"
                    />
                    <Button onClick={generateDashboard}>Generate with AI</Button>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline"><Layout className="w-4 h-4 mr-2" /> Layout</Button>
                    <Button><Save className="w-4 h-4 mr-2" /> Save Dashboard</Button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-4">
                {widgets.map((w) => (
                    <Card key={w.id} className={`${w.type === 'kpi' ? 'col-span-3' : 'col-span-6'} min-h-[200px]`}>
                        <CardHeader className="py-3">
                            <CardTitle className="text-sm font-medium">{w.title}</CardTitle>
                        </CardHeader>
                        <CardContent className="flex items-center justify-center h-full">
                            {w.type === 'kpi' && <span className="text-3xl font-bold">{w.value}</span>}
                            {w.type === 'chart' && (
                                <div className="w-full h-32 bg-muted/50 rounded flex items-center justify-center">
                                    [AI Generated {w.chartType} Chart]
                                </div>
                            )}
                            {w.type === 'insight' && (
                                <div className="flex items-start gap-2 text-sm text-muted-foreground italic">
                                    <Brain className="w-4 h-4 text-blue-500 mt-1" />
                                    {w.content}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
};
