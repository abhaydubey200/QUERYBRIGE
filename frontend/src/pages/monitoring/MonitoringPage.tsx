import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Cpu, 
  Database, 
  HardDrive, 
  RefreshCcw, 
  CheckCircle2, 
  AlertCircle,
  Zap
} from 'lucide-react';

interface SystemStatus {
  services: {
    api: string;
    worker: string;
    ai_runtime: string;
    db: string;
  };
  resources: {
    cpu: string;
    memory: string;
    memory_available_mb: number;
    disk: string;
  };
  uptime: string;
  load: string;
}

const MonitoringPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/monitoring/status`);
      const data = await response.json();
      setStatus(data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading || !status) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
          <p className="text-slate-400 animate-pulse">Initializing System Telemetry...</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (s: string) => {
    switch (s.toLowerCase()) {
      case 'healthy':
      case 'active':
      case 'connected':
        return 'text-emerald-400 bg-emerald-400/10';
      default:
        return 'text-amber-400 bg-amber-400/10';
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">System Monitoring</h1>
          <p className="text-slate-400 mt-2">Real-time infrastructure health and resource utilization</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Last Sync</p>
            <p className="text-sm text-slate-300">{lastUpdated.toLocaleTimeString()}</p>
          </div>
          <button 
            onClick={() => { setLoading(true); fetchStatus(); }}
            className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/10"
          >
            <RefreshCcw className={`w-5 h-5 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Resource Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ResourceCard 
          title="CPU Usage" 
          value={status.resources.cpu} 
          icon={<Cpu className="w-6 h-6 text-blue-400" />} 
          trend="Nominal"
          color="blue"
        />
        <ResourceCard 
          title="Memory" 
          value={status.resources.memory} 
          icon={<Activity className="w-6 h-6 text-purple-400" />} 
          trend={`${status.resources.memory_available_mb}MB Free`}
          color="purple"
        />
        <ResourceCard 
          title="Disk Storage" 
          value={status.resources.disk} 
          icon={<HardDrive className="w-6 h-6 text-emerald-400" />} 
          trend="Storage Healthy"
          color="emerald"
        />
        <ResourceCard 
          title="System Uptime" 
          value={status.uptime} 
          icon={<Zap className="w-6 h-6 text-amber-400" />} 
          trend="Continuous"
          color="amber"
        />
      </div>

      {/* Services and Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-slate-900/50 rounded-2xl border border-white/5 p-6 backdrop-blur-sm">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-blue-400" />
            Service Health Status
          </h2>
          <div className="space-y-4">
            {Object.entries(status.services).map(([service, state]) => (
              <div key={service} className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                  <span className="text-slate-200 font-medium capitalize">{service.replace('_', ' ')}</span>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusColor(state)}`}>
                  {state}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/50 rounded-2xl border border-white/5 p-6 backdrop-blur-sm flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              Runtime Intelligence
            </h2>
            <div className="space-y-6">
              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Current Load Factor</span>
                  <span className={`font-bold ${status.load === 'nominal' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {status.load.toUpperCase()}
                  </span>
                </div>
                <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-1000 ${status.load === 'nominal' ? 'bg-emerald-500' : 'bg-amber-500'}`}
                    style={{ width: status.resources.cpu }}
                  />
                </div>
              </div>
              
              <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                <p className="text-xs text-blue-300/80 leading-relaxed">
                  QueryBridge AI Runtime is optimized for low-latency inference. 
                  Current throughput capacity is at 100%.
                </p>
              </div>
            </div>
          </div>
          
          <button className="w-full mt-8 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-300 text-sm font-medium transition-all">
            View Advanced Logs
          </button>
        </div>
      </div>
    </div>
  );
};

const ResourceCard = ({ title, value, icon, trend, color }: any) => {
  const colorMap: any = {
    blue: 'from-blue-500/20 to-transparent border-blue-500/20',
    purple: 'from-purple-500/20 to-transparent border-purple-500/20',
    emerald: 'from-emerald-500/20 to-transparent border-emerald-500/20',
    amber: 'from-amber-500/20 to-transparent border-amber-500/20'
  };

  const glowColor: any = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500'
  };

  return (
    <div className={`bg-slate-900/50 p-6 rounded-2xl border backdrop-blur-sm relative overflow-hidden transition-all hover:translate-y-[-2px] ${colorMap[color]}`}>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-white/5 rounded-lg border border-white/5">
            {icon}
          </div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
          <span className="text-xs text-slate-400 mt-1 font-medium">{trend}</span>
        </div>
      </div>
      <div className={`absolute -right-4 -bottom-4 w-24 h-24 blur-3xl opacity-20 ${glowColor[color]}`} />
    </div>
  );
};

export default MonitoringPage;
