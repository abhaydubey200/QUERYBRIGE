import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Database, Search, Filter, RefreshCw, ChevronRight, 
  Table as TableIcon, Eye, Shield, Activity, Share2, AlertCircle, Star
} from 'lucide-react';
import { useConnectionStore } from '../../store/connectionStore';
import { getApiClient } from '../../services/aiSchemaApi';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL;

export default function CatalogExplorerPage() {
  const { connections, fetchConnections } = useConnectionStore();
  const [selectedConnection, setSelectedConnection] = useState<string | null>(null);
  const [tables, setTables] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const apiClient = getApiClient();
  const [entityCache, setEntityCache] = useState<Record<string, any>>({});
  const [anomalyCache, setAnomalyCache] = useState<Record<string, any>>({});

  useEffect(() => {
    fetchConnections();
  }, []);

  useEffect(() => {
    if (selectedConnection) {
      loadTables(selectedConnection);
    }
  }, [selectedConnection]);

  // Load AI schema information for tables in background
  useEffect(() => {
    if (tables.length === 0) return;

    tables.forEach(async (table) => {
      try {
        // Cache semantic entity info
        if (!entityCache[table.id]) {
          const entity = await apiClient.getSemanticEntity(table.id);
          setEntityCache((prev) => ({ ...prev, [table.id]: entity }));
        }

        // Cache anomaly info
        if (!anomalyCache[table.id]) {
          const anomalies = await apiClient.getTableAnomalies(table.id, 30);
          setAnomalyCache((prev) => ({ ...prev, [table.id]: anomalies }));
        }
      } catch (error) {
        console.debug(`Failed to load AI schema for table ${table.id}`);
      }
    });
  }, [tables, apiClient]);

  const loadTables = async (connId: string) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/catalog/tables/${connId}`);
      setTables(response.data);
      // Clear caches when loading new tables
      setEntityCache({});
      setAnomalyCache({});
    } catch (error) {
      console.error('Failed to load tables', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!selectedConnection) return;
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/catalog/refresh`, { connection_id: selectedConnection });
      // In a real app, we'd poll or use a websocket. For now, we wait and reload.
      setTimeout(() => loadTables(selectedConnection), 5000);
    } catch (error) {
      console.error('Refresh failed', error);
      setLoading(false);
    }
  };

  const filteredTables = tables.filter(t => 
    t.table_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.schema_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-[#0a0a0c] text-slate-300 overflow-hidden">
      {/* Sidebar: Connections */}
      <div className="w-80 border-r border-slate-800/50 bg-[#0d0d0f] flex flex-col">
        <div className="p-6 border-b border-slate-800/50">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-500" />
            Catalog Explorer
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {connections.map(conn => (
            <button
              key={conn.id}
              onClick={() => setSelectedConnection(conn.id)}
              className={`w-full text-left p-3 rounded-lg transition-all border ${
                selectedConnection === conn.id 
                  ? 'bg-blue-500/10 border-blue-500/50 text-white' 
                  : 'border-transparent hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${conn.status === 'online' ? 'bg-green-500' : 'bg-slate-600'}`} />
                <span className="font-medium">{conn.name}</span>
                <span className="ml-auto text-[10px] uppercase tracking-wider text-slate-500">{conn.db_type}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content: Tables Grid */}
      <div className="flex-1 flex flex-col">
        <div className="p-6 border-b border-slate-800/50 bg-[#0d0d0f]/50 flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input 
                type="text"
                placeholder="Search tables, schemas, or entities..."
                className="w-full bg-slate-900/50 border border-slate-800 rounded-lg py-2 pl-10 pr-4 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="p-2 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all">
              <Filter className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={handleRefresh}
              disabled={loading || !selectedConnection}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Sync Metadata
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-8">
          {!selectedConnection ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500">
              <Database className="w-16 h-16 mb-4 opacity-10" />
              <p className="text-lg">Select a connection to explore its catalog</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredTables.map(table => (
                <div 
                  key={table.id}
                  onClick={() => navigate(`/catalog/table/${table.id}`)}
                  className="group bg-[#121214] border border-slate-800/50 rounded-xl p-5 hover:border-blue-500/50 hover:bg-[#16161a] transition-all cursor-pointer relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-all">
                    <ChevronRight className="w-4 h-4 text-blue-500" />
                  </div>

                  <div className="flex items-start gap-4 mb-4">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                      <TableIcon className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="flex-1">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">
                        {table.schema_name}
                      </div>
                      <h3 className="font-bold text-white group-hover:text-blue-400 transition-colors truncate w-40">
                        {table.table_name}
                      </h3>
                    </div>
                    {/* Anomaly Alert Badge */}
                    {anomalyCache[table.id] && anomalyCache[table.id].count > 0 && (
                      <div className="ml-auto">
                        <AlertCircle className="w-4 h-4 text-orange-500" title={`${anomalyCache[table.id].count} anomalies detected`} />
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Rows</span>
                      <span className="text-slate-300 font-mono">{(table.row_count_estimate || 0).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Type</span>
                      <span className="text-slate-400 px-2 py-0.5 bg-slate-800 rounded uppercase text-[10px]">
                        {entityCache[table.id]?.entity_type || table.entity_type || 'Unknown'}
                      </span>
                    </div>
                    {entityCache[table.id] && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">Confidence</span>
                        <span className="text-yellow-400 flex items-center gap-1">
                          <Star className="w-3 h-3" />
                          {Math.round((entityCache[table.id]?.confidence || 0) * 100)}%
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-800/50 flex items-center justify-between opacity-50 group-hover:opacity-100 transition-all">
                    <div className="flex gap-2">
                      <Shield className="w-3 h-3 text-slate-500" />
                      <Activity className="w-3 h-3 text-slate-500" />
                      <Share2 className="w-3 h-3 text-slate-500" />
                    </div>
                    <span className="text-[10px] text-slate-600">
                      Sync: {new Date(table.last_metadata_sync).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
