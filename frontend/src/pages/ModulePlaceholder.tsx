import React from 'react';
import { useLocation } from 'react-router-dom';

const ModulePlaceholder = ({ title, icon: Icon }: any) => {
  const location = useLocation();
  
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
      <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center text-gray-500 border border-white/5">
        <Icon size={40} />
      </div>
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">{title} Module</h1>
        <p className="text-gray-500 max-w-md">
          The <span className="text-blue-400 font-mono">{location.pathname}</span> engine is currently initializing in the background. 
          Hardware acceleration and semantic grounding are active.
        </p>
      </div>
      <div className="flex gap-4">
        <div className="px-4 py-2 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-xl text-xs font-bold uppercase tracking-wider">
          Runtime Ready
        </div>
        <div className="px-4 py-2 bg-blue-500/10 text-blue-500 border border-blue-500/20 rounded-xl text-xs font-bold uppercase tracking-wider">
          v2.1.0-ENTERPRISE
        </div>
      </div>
    </div>
  );
};

export default ModulePlaceholder;
