import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Users, Search, Clock } from 'lucide-react';

const AuditLogsPage = () => {
  const logs = [
    { id: 1, user: 'admin@querybridge.io', action: 'QUERY_EXECUTE', resource: 'sales_data', timestamp: '2 mins ago' },
    { id: 2, user: 'engineer@querybridge.io', action: 'CONNECTION_CREATE', resource: 'Snowflake_PROD', timestamp: '15 mins ago' },
    { id: 3, user: 'admin@querybridge.io', action: 'RBAC_UPDATE', resource: 'Role:Analyst', timestamp: '1 hour ago' },
  ];

  return (
    <div className="p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Audit Logs</h1>
          <p className="text-gray-400">Security event tracking and compliance history.</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg">
          <Search size={18} className="text-gray-500" />
          <input className="bg-transparent outline-none text-sm" placeholder="Search logs..." />
        </div>
      </header>

      <Card className="bg-[#0a0a0a] border-white/5">
        <CardContent className="p-0">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 bg-white/[0.02]">
                <th className="p-4 text-xs font-bold uppercase tracking-widest text-gray-500">User</th>
                <th className="p-4 text-xs font-bold uppercase tracking-widest text-gray-500">Action</th>
                <th className="p-4 text-xs font-bold uppercase tracking-widest text-gray-500">Resource</th>
                <th className="p-4 text-xs font-bold uppercase tracking-widest text-gray-500">Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                  <td className="p-4 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-500">
                      <Users size={14} />
                    </div>
                    <span className="text-gray-300 font-medium">{log.user}</span>
                  </td>
                  <td className="p-4 text-gray-400 font-mono text-xs">{log.action}</td>
                  <td className="p-4 text-gray-300">{log.resource}</td>
                  <td className="p-4 text-gray-500 flex items-center gap-2">
                    <Clock size={14} /> {log.timestamp}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditLogsPage;
