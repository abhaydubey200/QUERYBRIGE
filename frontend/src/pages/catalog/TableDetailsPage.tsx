import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ChevronLeft, Table as TableIcon, Columns, BarChart3, 
  GitBranch, Shield, Zap, Search, Download, 
  MoreVertical, Info, ExternalLink, AlertCircle
} from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL;

export default function TableDetailsPage() {
  const { tableId } = useParams();
  const navigate = useNavigate();
  const [table, setTable] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'columns' | 'profiling' | 'lineage' | 'relationships'>('columns');

  useEffect(() => {
    loadTableDetails();
  }, [tableId]);

  const loadTableDetails = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/catalog/table/${tableId}`);
      setTable(response.data);
    } catch (error) {
      console.error('Failed to load table details', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfile = async () => {
    try {
      await axios.post(`${API_BASE}/catalog/profile/${tableId}`);
      alert('Profiling started in background');
    } catch (error) {
      alert('Failed to start profiling');
    }
  };

  if (loading) return (
    <div className="h-screen flex items-center justify-center bg-[#0a0a0c] text-white">
      <Zap className="w-8 h-8 text-blue-500 animate-pulse" />
    </div>
  );

  if (!table) return <div>Table not found</div>;

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-300">
      {/* Header */}
      <div className="border-b border-slate-800/50 bg-[#0d0d0f]/80 backdrop-blur-xl sticky top-0 z-30">
        <div className="px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button 
              onClick={() => navigate('/catalog')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-all"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 rounded-xl">
                <TableIcon className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium mb-1">
                  <span>{table.schema_name}</span>
                  <span className="w-1 h-1 bg-slate-700 rounded-full" />
                  <span className="uppercase text-[10px] tracking-widest">{table.entity_type}</span>
                </div>
                <h1 className="text-2xl font-bold text-white tracking-tight">{table.table_name}</h1>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={handleProfile}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all"
            >
              <BarChart3 className="w-4 h-4" />
              Run Profiler
            </button>
            <button className="p-2 border border-slate-800 rounded-lg hover:bg-slate-800 transition-all">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-8 flex gap-8">
          {[
            { id: 'columns', label: 'Schema', icon: Columns },
            { id: 'profiling', label: 'Profiling', icon: BarChart3 },
            { id: 'relationships', label: 'Relationships', icon: GitBranch },
            { id: 'lineage', label: 'Lineage', icon: Zap },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-4 border-b-2 transition-all font-medium text-sm ${
                activeTab === tab.id 
                  ? 'border-blue-500 text-blue-500' 
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-8">
        {activeTab === 'columns' && (
          <div className="bg-[#0d0d0f] border border-slate-800/50 rounded-2xl overflow-hidden shadow-2xl">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/50 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                  <th className="px-6 py-4">#</th>
                  <th className="px-6 py-4">Column Name</th>
                  <th className="px-6 py-4">Data Type</th>
                  <th className="px-6 py-4">Nullable</th>
                  <th className="px-6 py-4">Governance</th>
                  <th className="px-6 py-4">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {table.columns?.map((col: any) => (
                  <tr key={col.id} className="hover:bg-slate-800/30 transition-all group">
                    <td className="px-6 py-4 text-xs text-slate-600 font-mono">{col.ordinal_position}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">{col.name}</span>
                        {col.is_primary_key && (
                          <span className="px-2 py-0.5 bg-yellow-500/10 text-yellow-500 text-[10px] rounded border border-yellow-500/20 font-bold">PK</span>
                        )}
                        {col.is_foreign_key && (
                          <span className="px-2 py-0.5 bg-purple-500/10 text-purple-500 text-[10px] rounded border border-purple-500/20 font-bold">FK</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-xs text-blue-400 bg-blue-500/5 px-2 py-1 rounded">{col.data_type}</code>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs ${col.is_nullable ? 'text-green-500' : 'text-slate-500'}`}>
                        {col.is_nullable ? 'YES' : 'NO'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {col.pii_tag ? (
                        <div className="flex items-center gap-2">
                          <Shield className="w-3 h-3 text-red-500" />
                          <span className="px-2 py-0.5 bg-red-500/10 text-red-500 text-[10px] rounded border border-red-500/20 font-bold uppercase">
                            {col.pii_tag}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-700 text-[10px] italic">No PII Detected</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {col.description || <span className="opacity-20 italic">No description</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'profiling' && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-[#0d0d0f] p-6 rounded-2xl border border-slate-800/50 shadow-lg">
                <div className="text-xs text-slate-500 font-bold uppercase tracking-widest mb-2">Total Rows</div>
                <div className="text-3xl font-black text-white">{(table.row_count_estimate || 0).toLocaleString()}</div>
              </div>
              {/* More Summary stats... */}
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Column profiling cards would go here */}
              <div className="h-64 flex items-center justify-center border-2 border-dashed border-slate-800 rounded-2xl text-slate-600 italic">
                <AlertCircle className="w-5 h-5 mr-2" />
                Run profiler to generate column-level statistics
              </div>
            </div>
          </div>
        )}

        {/* Other tabs follow same premium pattern... */}
      </div>
    </div>
  );
}
