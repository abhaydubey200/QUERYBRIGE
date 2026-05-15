import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/table';

const SemanticPage: React.FC = () => {
    const { connections } = useWorkspaceStore();
    const [metrics, setMetrics] = useState<any[]>([]);
    const [newMetric, setNewMetric] = useState({ name: '', formula: '', description: '' });

    const handleAddMetric = () => {
        setMetrics([...metrics, { ...newMetric, id: Math.random().toString() }]);
        setNewMetric({ name: '', formula: '', description: '' });
    };

    return (
        <div className="p-6 space-y-6">
            <h1 className="text-3xl font-bold">Semantic Layer</h1>
            <p className="text-gray-400">Define and govern your business metrics and dimensions.</p>

            <div className="grid grid-cols-3 gap-6">
                <Card className="col-span-1">
                    <CardHeader>
                        <CardTitle>Define New Metric</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Input 
                            placeholder="Metric Name (e.g. Total Revenue)" 
                            value={newMetric.name}
                            onChange={(e) => setNewMetric({...newMetric, name: e.target.value})}
                        />
                        <Textarea 
                            placeholder="SQL Formula (e.g. SUM(price * qty))" 
                            value={newMetric.formula}
                            onChange={(e) => setNewMetric({...newMetric, formula: e.target.value})}
                        />
                        <Input 
                            placeholder="Description" 
                            value={newMetric.description}
                            onChange={(e) => setNewMetric({...newMetric, description: e.target.value})}
                        />
                        <Button className="w-full" onClick={handleAddMetric}>Save Metric</Button>
                    </CardContent>
                </Card>

                <Card className="col-span-2">
                    <CardHeader>
                        <CardTitle>Metric Registry</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Formula</TableCell>
                                    <TableCell>Description</TableCell>
                                    <TableCell>Status</TableCell>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {metrics.map((m) => (
                                    <TableRow key={m.id}>
                                        <TableCell className="font-medium">{m.name}</TableCell>
                                        <TableCell><code>{m.formula}</code></TableCell>
                                        <TableCell>{m.description}</TableCell>
                                        <TableCell>
                                            <span className="px-2 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full text-xs font-bold">Governed</span>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default SemanticPage;
