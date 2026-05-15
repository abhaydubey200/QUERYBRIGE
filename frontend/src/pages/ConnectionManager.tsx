import React from 'react';
import { motion } from 'framer-motion';
import { Database, Plus, ShieldCheck } from 'lucide-react';

const ConnectionManager: React.FC = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center mb-12"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">Data Infrastructure</h1>
          <p className="text-gray-400">Manage your enterprise database connections and security profiles.</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/20">
          <Plus size={20} />
          New Connection
        </button>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.02 }}
            className="bg-[#111] border border-white/10 p-6 rounded-2xl hover:border-blue-500/50 transition-colors cursor-pointer group"
          >
            <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
              <Database className="text-blue-500" size={24} />
            </div>
            <h3 className="text-xl font-semibold text-white mb-1">Production Warehouse {i}</h3>
            <p className="text-gray-500 text-sm mb-4">PostgreSQL • aws-us-east-1</p>
            <div className="flex items-center gap-2 text-xs text-green-400 bg-green-400/10 w-fit px-2 py-1 rounded-full">
              <ShieldCheck size={12} />
              SSL SECURED
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default ConnectionManager;
