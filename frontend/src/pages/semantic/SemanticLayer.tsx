import React from 'react';
import { motion } from 'framer-motion';
import { Network, Zap, ShieldCheck, Database, Search, ArrowUpRight } from 'lucide-react';

const SemanticLayer = () => {
  return (
    <div className="space-y-10">
      <header>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-blue-600/10 border border-blue-500/20 rounded-2xl flex items-center justify-center text-blue-500 shadow-lg shadow-blue-500/5">
            <Network size={24} />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Semantic Engine</h1>
            <p className="text-gray-400 text-sm">Unified business logic and metric resolution layer.</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Active Metrics */}
          <div className="bg-[#0d0d0d] border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
              <h2 className="font-bold flex items-center gap-2">
                <Zap size={18} className="text-yellow-500" />
                Certified Business Metrics
              </h2>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input 
                  type="text" 
                  placeholder="Filter metrics..." 
                  className="bg-black border border-white/10 rounded-full py-1.5 pl-9 pr-4 text-xs focus:outline-none focus:border-blue-500/50"
                />
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <MetricRow name="Monthly Recurring Revenue" formula="SUM(mrr)" owner="Finance" status="certified" />
              <MetricRow name="Customer Churn Rate" formula="1 - (active_at_end / active_at_start)" owner="Growth" status="certified" />
              <MetricRow name="Net Promoter Score" formula="AVG(score)" owner="Product" status="draft" />
            </div>
          </div>

          {/* Semantic Graph */}
          <div className="bg-[#0d0d0d] border border-white/5 rounded-3xl p-8 h-[400px] flex flex-col items-center justify-center relative overflow-hidden group">
             <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(37,99,235,0.1)_0%,transparent_70%)] opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
             <Network size={64} className="text-white/10 mb-6 group-hover:scale-110 transition-transform duration-700" />
             <h3 className="text-lg font-bold text-white mb-2">Live Semantic Graph</h3>
             <p className="text-gray-500 text-sm text-center max-w-sm">The Knowledge Graph is mapping 1,402 relationships across 4 major data sources.</p>
             <button className="mt-8 px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-sm font-bold hover:bg-white/10 transition-all">Open Visualizer</button>
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-gradient-to-br from-blue-600/20 to-transparent border border-blue-500/20 rounded-3xl p-6">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
              <ShieldCheck size={18} className="text-blue-400" />
              Governance & Lineage
            </h3>
            <p className="text-gray-400 text-xs leading-relaxed mb-6">
              Metrics in the semantic layer are protected by attribute-based access control (ABAC). 
              Lineage is automatically tracked back to raw SQL origins.
            </p>
            <div className="space-y-3">
               <StatusItem label="Data Integrity" status="Healthy" />
               <StatusItem label="Lineage Sync" status="Real-time" />
               <StatusItem label="Certifications" status="4 Active" />
            </div>
          </div>

          <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-6">
            <h3 className="font-bold text-white mb-4">Discovery</h3>
            <div className="space-y-2">
              {['Inventory Model', 'Revenue Projections', 'User Behavior'].map(item => (
                <div key={item} className="flex items-center justify-between p-3 rounded-xl bg-black border border-white/5 hover:border-blue-500/30 transition-all group cursor-pointer">
                  <span className="text-sm font-medium">{item}</span>
                  <ArrowUpRight size={14} className="text-gray-600 group-hover:text-blue-500" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricRow = ({ name, formula, owner, status }: any) => (
  <div className="flex items-center justify-between p-4 bg-black/40 border border-white/5 rounded-2xl hover:border-blue-500/20 transition-all group">
    <div className="flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-blue-500/5 border border-blue-500/10 flex items-center justify-center text-blue-500">
        <Database size={18} />
      </div>
      <div>
        <h4 className="font-bold text-sm text-gray-200 group-hover:text-blue-400 transition-colors">{name}</h4>
        <code className="text-[10px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">{formula}</code>
      </div>
    </div>
    <div className="flex items-center gap-6">
      <div className="text-right">
        <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Owner</p>
        <p className="text-xs text-gray-300 font-medium">{owner}</p>
      </div>
      <div className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${
        status === 'certified' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
      }`}>
        {status}
      </div>
    </div>
  </div>
);

const StatusItem = ({ label, status }: any) => (
  <div className="flex items-center justify-between text-xs">
    <span className="text-gray-500">{label}</span>
    <span className="font-bold text-white">{status}</span>
  </div>
);

export default SemanticLayer;
