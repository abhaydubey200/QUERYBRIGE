import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Database, 
  Activity, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Search, 
  Filter,
  Zap,
  MoreVertical,
  Trash2,
  Settings2,
  ExternalLink
} from 'lucide-react';
import ConnectionWizard from './ConnectionWizard';
import SchemaExplorer from './SchemaExplorer';
import { useConnectionStore } from '../../store/connectionStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const ConnectionDashboard = () => {
  const [showWizard, setShowWizard] = useState(false);
  const [exploringId, setExploringId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const { connections, setConnections, loading, setLoading, error, setError } = useConnectionStore();

  const fetchConnections = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/connections/`, { signal });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error?.message || `Connection list failed (${response.status})`);
      }
      const result = await response.json();
      if (result.success) {
        setConnections(result.data || []);
      } else {
        throw new Error(result.error?.message || 'Failed to fetch connections');
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      console.error('Failed to fetch connections', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch connections');
    } finally {
      setLoading(false);
    }
  }, [setConnections, setLoading, setError]);

  useEffect(() => {
    const controller = new AbortController();
    fetchConnections(controller.signal);
    return () => controller.abort();
  }, [fetchConnections]);

  const stats = [
    { label: 'Total Connections', value: connections.length.toString(), icon: Database, color: 'text-blue-500' },
    { label: 'Active', value: connections.filter(c => c.status === 'online' || c.is_active || c.status === 'active').length.toString(), icon: CheckCircle2, color: 'text-emerald-500' },
    { label: 'Failed', value: connections.filter(c => c.status === 'offline' || c.status === 'degraded' || c.status === 'error').length.toString(), icon: AlertCircle, color: 'text-rose-500' },
    { label: 'Avg Latency', value: 'Live', icon: Clock, color: 'text-amber-500' },
  ];

  const filteredConnections = connections.filter(c => 
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.type || c.db_type || '').toLowerCase().includes(search.toLowerCase()) ||
    c.host.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Data Connections</h1>
          <p className="text-gray-400">Manage and monitor your enterprise data sources with AI intelligence.</p>
        </div>
        <button 
          onClick={() => setShowWizard(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-blue-900/20"
        >
          <Plus size={20} />
          Create New Connection
        </button>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        {stats.map((stat, i) => (
          <motion.div 
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-[#1a1a1a] border border-gray-800 p-6 rounded-2xl hover:border-gray-700 transition-colors group"
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl bg-gray-900 ${stat.color}`}>
                <stat.icon size={24} />
              </div>
              <Activity size={16} className="text-gray-600 group-hover:text-blue-500 transition-colors" />
            </div>
            <p className="text-gray-400 text-sm font-medium">{stat.label}</p>
            <h3 className="text-3xl font-bold mt-1">{stat.value}</h3>
          </motion.div>
        ))}
      </div>

      {/* Filters & Search */}
      <div className="flex gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
          <input 
            type="text" 
            placeholder="Search connections by name, type, or host..."
            className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button className="flex items-center gap-2 bg-[#1a1a1a] border border-gray-800 px-6 rounded-xl hover:bg-gray-800 transition-colors">
          <Filter size={18} />
          Filter
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300 flex items-center gap-3">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Connection Grid */}
      <div className="flex gap-6 items-start">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
          {loading ? (
            Array(3).fill(0).map((_, i) => (
              <div key={i} className="h-64 bg-[#1a1a1a] animate-pulse rounded-2xl border border-gray-800" />
            ))
          ) : filteredConnections.length > 0 ? (
            filteredConnections.map((conn) => (
              <ConnectionCard
                key={conn.id}
                id={conn.id}
                name={conn.name}
                type={conn.type || conn.db_type}
                status={conn.status || (conn.is_active ? 'online' : 'offline')}
                host={`${conn.host}${conn.port ? `:${conn.port}` : ''}`}
                latency={conn.latency_ms ? `${conn.latency_ms}ms` : 'Probe'}
                health={conn.status === 'degraded' ? 55 : conn.status === 'offline' ? 0 : 98}
                onDelete={fetchConnections}
                onExplore={() => setExploringId(conn.id)}
              />
            ))
          ) : (
            <div className="col-span-full py-20 text-center bg-[#1a1a1a] rounded-2xl border border-dashed border-gray-800">
              <Database size={48} className="mx-auto text-gray-700 mb-4" />
              <h3 className="text-xl font-bold text-gray-400">No connections found</h3>
              <p className="text-gray-500 mt-2">Create a connection to start browsing schemas.</p>
            </div>
          )}
        </div>
        {exploringId && (
          <div className="sticky top-8 h-[calc(100vh-4rem)]">
            <SchemaExplorer connectionId={exploringId} onClose={() => setExploringId(null)} />
          </div>
        )}
      </div>

      {/* Wizard Modal */}
      <AnimatePresence>
        {showWizard && (
          <ConnectionWizard 
            onClose={() => setShowWizard(false)} 
            onSuccess={fetchConnections}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

const ConnectionCard = ({ id, name, type, status, host, latency, health, onDelete, onExplore }: any) => {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this connection?')) return;
    setDeleting(true);
    try {
      await fetch(`${API_URL}/connections/${id}`, { method: 'DELETE' });
      onDelete();
    } catch (error) {
      console.error('Delete failed', error);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <motion.div 
      layout
      whileHover={{ y: -5 }}
      className={`bg-[#1a1a1a] border border-gray-800 rounded-2xl p-6 relative overflow-hidden group ${deleting ? 'opacity-50 grayscale' : ''}`}
    >
      <div className="flex justify-between items-start mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gray-900 rounded-xl group-hover:bg-blue-600/10 transition-colors">
            <Database size={24} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold group-hover:text-blue-400 transition-colors line-clamp-1">{name}</h3>
            <span className="text-sm text-gray-500 uppercase tracking-wider font-semibold">{type}</span>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tighter ${
          status === 'online' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
        }`}>
          {status}
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Endpoint</span>
          <span className="font-mono text-gray-300 truncate max-w-[150px]">{host}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Latency</span>
          <span className="font-mono text-gray-300">{latency}</span>
        </div>
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">Health Score</span>
            <span className="text-emerald-500">{health}%</span>
          </div>
          <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${health}%` }}
              className={`h-full ${health > 80 ? 'bg-emerald-500' : 'bg-rose-500'}`}
            />
          </div>
        </div>
      </div>

      <div className="mt-8 flex justify-between items-center">
        <div className="flex items-center gap-1">
          <button 
            onClick={handleDelete}
            className="p-2 text-gray-500 hover:text-rose-500 transition-colors"
          >
            <Trash2 size={18} />
          </button>
          <button className="p-2 text-gray-500 hover:text-white transition-colors">
            <Settings2 size={18} />
          </button>
        </div>
        <button onClick={onExplore} className="text-sm font-semibold text-blue-500 hover:text-blue-400 transition-colors flex items-center gap-1">
          Explore <ExternalLink size={14} />
        </button>
      </div>

      {/* Decorative Gradient Overlay */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[80px] pointer-events-none group-hover:bg-blue-500/10 transition-colors" />
    </motion.div>
  );
};

export default ConnectionDashboard;
