import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ChevronRight, 
  ChevronDown, 
  Table, 
  Columns, 
  Search, 
  Database,
  Shield,
  Key,
  Info,
  Zap
} from 'lucide-react';

const SchemaExplorer = ({ data }: any) => {
  const [expanded, setExpanded] = useState<string[]>([]);
  const [search, setSearch] = useState('');

  const toggle = (id: string) => {
    setExpanded(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="h-full flex flex-col bg-[#0d0d0d] border border-gray-800 rounded-3xl overflow-hidden">
      {/* Sidebar Search */}
      <div className="p-6 border-b border-gray-800/50">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
          <input 
            type="text" 
            placeholder="Search schemas, tables..."
            className="w-full bg-[#141414] border border-gray-800 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {data?.map((schema: any) => (
          <div key={schema.name} className="space-y-1">
            <div 
              onClick={() => toggle(schema.name)}
              className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer group"
            >
              {expanded.includes(schema.name) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <Database size={16} className="text-blue-400" />
              <span className="text-sm font-bold tracking-tight text-gray-300 group-hover:text-white transition-colors">
                {schema.name}
              </span>
            </div>

            {expanded.includes(schema.name) && (
              <div className="ml-6 space-y-1 border-l border-gray-800 pl-2">
                {schema.tables.map((table: any) => (
                  <div key={table.name}>
                    <div 
                      onClick={() => toggle(`${schema.name}.${table.name}`)}
                      className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer group"
                    >
                      {expanded.includes(`${schema.name}.${table.name}`) ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <Table size={14} className="text-emerald-400" />
                      <span className="text-sm font-medium text-gray-400 group-hover:text-white transition-colors">
                        {table.name}
                      </span>
                    </div>

                    {expanded.includes(`${schema.name}.${table.name}`) && (
                      <div className="ml-6 space-y-0.5 border-l border-gray-800/50 pl-2 py-1">
                        {table.columns.map((col: any) => (
                          <div key={col.name} className="flex items-center justify-between p-1.5 hover:bg-white/5 rounded-md text-[11px] group">
                            <div className="flex items-center gap-2">
                              <Columns size={12} className="text-gray-600" />
                              <span className="text-gray-400 font-mono">{col.name}</span>
                            </div>
                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              {col.isPrimaryKey && <Key size={10} className="text-amber-500" />}
                              <span className="bg-gray-800 text-gray-500 px-1.5 rounded uppercase font-bold text-[9px]">
                                {col.type}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* AI Context Panel (Bottom) */}
      <div className="p-6 bg-blue-600/5 border-t border-blue-500/10">
        <div className="flex items-center gap-2 text-blue-400 mb-3">
          <Zap size={14} fill="currentColor" />
          <span className="text-xs font-bold uppercase tracking-wider">AI Intelligence</span>
        </div>
        <p className="text-[11px] text-gray-400 leading-relaxed italic">
          "This schema appears to be part of a Sales CRM. Highly indexed on customer_id."
        </p>
      </div>
    </div>
  );
};

export default SchemaExplorer;
