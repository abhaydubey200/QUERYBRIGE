import React from 'react';
import { Search, Bell, Command, User, Shield, Share2 } from 'lucide-react';

const Topbar = () => {
  return (
    <div className="h-16 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl flex items-center justify-between px-8 sticky top-0 z-40">
      <div className="flex items-center gap-6 flex-1">
        <div className="relative w-96 group">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-blue-500 transition-colors" />
          <input 
            type="text" 
            placeholder="Search metadata, dashboards, or AI agents..." 
            className="w-full bg-white/5 border border-white/5 rounded-full py-2 pl-12 pr-4 text-sm text-gray-300 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-1 bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
            <Command size={10} className="text-gray-500" />
            <span className="text-[10px] text-gray-500 font-bold">K</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">System Live</span>
        </div>

        <button className="p-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-all relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full border-2 border-[#0a0a0a]" />
        </button>

        <div className="h-6 w-px bg-white/10 mx-2" />

        <div className="flex items-center gap-3 pl-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-bold transition-all shadow-lg shadow-blue-600/20 active:scale-95">
            <Share2 size={16} />
            <span>Share</span>
          </button>
          
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 p-[1px]">
            <div className="w-full h-full rounded-[11px] bg-[#0a0a0a] flex items-center justify-center overflow-hidden">
              <User size={20} className="text-gray-400" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Topbar;
