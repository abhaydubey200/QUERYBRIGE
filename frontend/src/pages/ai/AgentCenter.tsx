import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Bot, MessageSquare, Shield, BrainCircuit, Activity, Settings2 } from 'lucide-react';

const AgentCenter = () => {
  return (
    <div className="space-y-10">
      <header className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-indigo-600/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center text-indigo-500 shadow-lg shadow-indigo-500/5">
              <Zap size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-white">Agent Center</h1>
              <p className="text-gray-400 text-sm">Deploy and manage autonomous enterprise reasoning agents.</p>
            </div>
          </div>
        </div>
        <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-sm transition-all shadow-xl shadow-indigo-600/20 active:scale-95">
          Deploy New Agent
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <AgentCard 
          name="Atlas-1 (Strategic Analyst)" 
          desc="Optimized for long-term forecasting and competitive landscape analysis."
          status="Active"
          tokens="1.2M / mo"
          health={100}
        />
        <AgentCard 
          name="Vigilant-X (Anomaly Bot)" 
          desc="Continuous monitoring of real-time telemetry and fraud patterns."
          status="Active"
          tokens="450k / mo"
          health={98}
        />
        <AgentCard 
          name="Scribe (Data Governance)" 
          desc="Automates PII discovery and audit log documentation."
          status="Idle"
          tokens="12k / mo"
          health={100}
        />
      </div>

      <div className="bg-[#0d0d0d] border border-white/5 rounded-3xl p-10 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-10 opacity-10">
          <BrainCircuit size={200} />
        </div>
        
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-2xl font-bold text-white mb-6">Autonomous Reasoning Hub</h2>
          <p className="text-gray-400 leading-relaxed mb-8">
            The Agent Center orchestrates multi-agent workflows using a "Shared Blackboard" architecture. 
            Agents can collaborate on complex reasoning tasks, execute SQL/Python, and self-correct based on grounded semantic metadata.
          </p>
          
          <div className="flex gap-4">
            <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl border border-white/10">
              <Activity size={16} className="text-emerald-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Memory: 4.2GB Cache</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl border border-white/10">
              <MessageSquare size={16} className="text-blue-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Logic: COT-v4</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AgentCard = ({ name, desc, status, tokens, health }: any) => (
  <div className="bg-[#0d0d0d] border border-white/5 rounded-3xl p-6 hover:border-indigo-500/30 transition-all group relative">
    <div className="flex justify-between items-start mb-6">
      <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-gray-400 group-hover:text-indigo-400 transition-colors">
        <Bot size={24} />
      </div>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${status === 'Active' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-gray-600'}`} />
        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{status}</span>
      </div>
    </div>
    
    <h3 className="font-bold text-white mb-2 group-hover:text-indigo-400 transition-colors">{name}</h3>
    <p className="text-gray-500 text-sm leading-relaxed mb-6">{desc}</p>
    
    <div className="pt-6 border-t border-white/5 flex justify-between items-center">
      <div>
        <p className="text-[10px] text-gray-600 font-bold uppercase tracking-wider">Usage</p>
        <p className="text-xs text-gray-300">{tokens}</p>
      </div>
      <button className="p-2 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all">
        <Settings2 size={16} className="text-gray-400" />
      </button>
    </div>
  </div>
);

export default AgentCenter;
