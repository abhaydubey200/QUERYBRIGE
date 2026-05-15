import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Database, 
  Table, 
  Columns, 
  ChevronRight, 
  Search, 
  RefreshCw,
  Loader2,
  FileCode,
  Layout,
  X,
  AlertCircle
} from 'lucide-react';

interface SchemaExplorerProps {
  connectionId: string;
  onClose: () => void;
}

const SchemaExplorer = ({ connectionId, onClose }: SchemaExplorerProps) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [tables, setTables] = useState<any[]>([]);
  const [search, setSearch] = useState('');

  const [truncated, setTruncated] = useState(false);

  const fetchMetadata = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/connections/${connectionId}/metadata`);
      if (!response.ok) throw new Error(`Metadata request failed (${response.status})`);
      const data = await response.json();
      setSchemas(data.schemas || []);
      setTables(data.tables || []);
      setTruncated(data.truncated || false);
      if (data.selected_schema) setSelectedSchema(data.selected_schema);
      else if (data.schemas?.length > 0) setSelectedSchema(data.schemas[0]);
    } catch (error) {
      console.error('Metadata fetch failed', error);
      setError(error instanceof Error ? error.message : 'Metadata fetch failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetadata();
  }, [connectionId]);

  const filteredTables = tables.filter(t => 
    (!selectedSchema || t.schema === selectedSchema) &&
    t.name.toLowerCase().includes(search.toLowerCase())
  ).slice(0, 500);

  return (
    <div className="flex h-full bg-[#111] border-l border-gray-800 w-[400px]">
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-[#1a1a1a]">
          <div className="flex items-center gap-2">
            <Layout size={18} className="text-blue-400" />
            <h3 className="font-bold text-sm uppercase tracking-wider">Catalog Explorer</h3>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={fetchMetadata} className="p-1 hover:bg-gray-800 rounded" aria-label="Refresh metadata">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
            <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded" aria-label="Close schema explorer">
              <X size={14} />
            </button>
          </div>
        </div>

        <div className="p-4 bg-gray-900/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={14} />
            <input 
              type="text" 
              placeholder="Search tables..."
              className="w-full bg-[#0a0a0a] border border-gray-800 rounded-lg py-2 pl-9 pr-4 text-sm focus:ring-1 focus:ring-blue-500 outline-none"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 gap-3">
              <Loader2 className="animate-spin text-blue-500" size={24} />
              <p className="text-xs text-gray-500">Crawling Metadata...</p>
            </div>
          ) : error ? (
            <div className="m-4 p-3 rounded-lg border border-red-500/20 bg-red-500/10 text-red-300 flex gap-2 text-xs">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          ) : (
            <div className="space-y-1 p-2">
              {schemas.map(schema => (
                <div key={schema} className="space-y-1">
                  <button 
                    onClick={() => setSelectedSchema(selectedSchema === schema ? null : schema)}
                    className="w-full flex items-center justify-between p-2 hover:bg-gray-800 rounded-lg transition-colors text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <Database size={14} className="text-amber-500" />
                      <span className="font-medium">{schema}</span>
                    </div>
                    <ChevronRight size={14} className={`transition-transform ${selectedSchema === schema ? 'rotate-90' : ''}`} />
                  </button>
                  
                  {selectedSchema === schema && (
                    <div className="ml-4 space-y-1 border-l border-gray-800 pl-2">
                      {filteredTables.length > 0 ? (
                        filteredTables.map(table => (
                          <div key={`${table.schema}.${table.name}`} className="p-2 flex items-center gap-2 text-xs text-gray-400 hover:text-white cursor-pointer transition-colors group">
                            <Table size={12} className="group-hover:text-blue-400" />
                            <span>{table.name}</span>
                          </div>
                        ))
                      ) : (
                        <p className="p-2 text-[10px] text-gray-600 italic">No tables found</p>
                      )}
                      
                      {truncated && (
                        <div className="p-2 mt-2 bg-amber-500/5 border border-amber-500/10 rounded-lg">
                          <p className="text-[9px] text-amber-500/80 leading-tight">
                            Results truncated for performance. Use search to find specific tables.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchemaExplorer;
