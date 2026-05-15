import React from 'react';
import { Shield, Activity, Users, Settings, Package, HardDrive } from 'lucide-react';

const AdminDashboard: React.FC = () => {
    const stats = [
        { label: 'Total Workspaces', value: '12', icon: <Package className="w-4 h-4" /> },
        { label: 'Active Users', value: '45', icon: <Users className="w-4 h-4" /> },
        { label: 'System Health', value: '99.9%', icon: <Activity className="w-4 h-4" /> },
        { label: 'Security Alerts', value: '0', icon: <Shield className="w-4 h-4" /> },
    ];

    return (
        <div className="p-8 space-y-8">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold">Enterprise Admin Center</h1>
                <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full text-xs font-bold">
                    <Activity className="w-3 h-3" /> System Online
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {stats.map(stat => (
                    <div key={stat.label} className="p-6 bg-card border rounded-2xl space-y-2">
                        <div className="text-muted-foreground flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                            {stat.icon} {stat.label}
                        </div>
                        <div className="text-2xl font-bold">{stat.value}</div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-6 bg-[#111] border border-white/10 rounded-2xl space-y-4">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <HardDrive className="w-5 h-5" /> Resource Governance
                    </h2>
                    <div className="space-y-4">
                        {['RAM Usage', 'CPU Load', 'Disk IO'].map(metric => (
                            <div key={metric} className="space-y-1">
                                <div className="flex justify-between text-xs font-medium">
                                    <span>{metric}</span>
                                    <span>45%</span>
                                </div>
                                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-[45%]" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="p-6 bg-[#111] border border-white/10 rounded-2xl space-y-4">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <Shield className="w-5 h-5" /> Security Policy Enforcement
                    </h2>
                    <div className="space-y-3">
                        {['Strict RBAC', 'AES-256 Storage', 'Refresh Token Rotation', 'PII Masking'].map(policy => (
                            <div key={policy} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                                <span className="text-sm font-medium">{policy}</span>
                                <div className="w-8 h-4 bg-blue-600 rounded-full relative">
                                    <div className="absolute right-1 top-1 w-2 h-2 bg-white rounded-full" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
