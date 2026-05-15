import React from 'react';
import { motion } from 'framer-motion';
import { Code2, Play, Save, Settings } from 'lucide-react';

const Workspace: React.FC = () => {
  return (
    <div className="flex h-screen bg-[#050505]">
      {/* Sidebar */}
      <div className="w-16 border-r border-white/10 flex flex-col items-center py-8 gap-8">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
          <Code2 className="text-white" size={24} />
        </div>
        <div className="flex flex-col gap-6 text-gray-500">
          <Settings size={24} className="hover:text-white cursor-pointer transition-colors" />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col p-8">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Semantic Query Editor</h1>
            <p className="text-gray-500 text-sm">Drafting queries against Production Warehouse</p>
          </div>
          <div className="flex gap-4">
            <button className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm font-medium transition-colors border border-white/10">
              <Save size={18} className="inline mr-2" />
              Save draft
            </button>
            <button className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-500/20">
              <Play size={18} className="inline mr-2" />
              Run Query
            </button>
          </div>
        </header>

        <div className="flex-1 bg-[#0a0a0a] rounded-2xl border border-white/10 p-6 font-mono text-sm text-blue-400">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <span className="text-purple-400">SELECT</span> * <span className="text-purple-400">FROM</span> business_metrics<br/>
            <span className="text-purple-400">WHERE</span> revenue {'>'} 1000000<br/>
            <span className="text-purple-400">ORDER BY</span> created_at <span className="text-purple-400">DESC</span>;
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Workspace;
