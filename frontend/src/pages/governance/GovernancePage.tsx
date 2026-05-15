import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Shield, Lock, FileCheck, Users } from 'lucide-react';

const GovernancePage = () => {
  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Governance & Security</h1>
        <p className="text-gray-400">Enterprise-grade data access controls and audit logging.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-[#111] border-gray-800">
          <CardHeader className="flex flex-row items-center gap-4">
            <Shield className="text-blue-500" />
            <CardTitle>Role Based Access Control</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-400 mb-4">Define granular permissions for connections and semantic models.</p>
            <div className="space-y-2">
              {['Admin', 'Data Engineer', 'Analyst', 'Viewer'].map(role => (
                <div key={role} className="flex justify-between p-3 bg-black/40 rounded-lg border border-gray-800">
                  <span className="text-white font-medium">{role}</span>
                  <span className="text-blue-400 text-xs font-bold uppercase tracking-widest">Active</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#111] border-gray-800">
          <CardHeader className="flex flex-row items-center gap-4">
            <Lock className="text-amber-500" />
            <CardTitle>Encryption Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl mb-4">
              <p className="text-emerald-500 font-bold flex items-center gap-2">
                <FileCheck size={18} />
                AES-256 FIELD-LEVEL ENCRYPTION ACTIVE
              </p>
            </div>
            <p className="text-gray-400 text-sm">
              All data source credentials are encrypted using the hardware-security-module backed key defined in your environment.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GovernancePage;
