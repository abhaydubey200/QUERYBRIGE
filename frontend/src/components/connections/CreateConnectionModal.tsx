import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Database, 
  ShieldCheck, 
  Globe, 
  Settings2,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Zap,
  Activity
} from 'lucide-react';

const CreateConnectionModal = ({ isOpen, onClose }: any) => {
  const [step, setStep] = useState(1);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    name: '',
    type: 'postgres',
    host: '',
    port: 5432,
    username: '',
    password: '',
    database: '',
    ssl: true,
  });

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    // Simulate API call
    setTimeout(() => {
      setIsTesting(false);
      setTestResult({ success: true, latency: '34ms' });
    }, 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
      />

      {/* Modal */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="relative w-full max-w-4xl bg-[#0f0f0f] border border-gray-800 rounded-3xl overflow-hidden shadow-2xl flex"
      >
        {/* Sidebar */}
        <div className="w-64 bg-[#141414] border-r border-gray-800 p-8 hidden md:block">
          <h2 className="text-xl font-bold mb-8">Setup Wizard</h2>
          <div className="space-y-6">
            <StepItem icon={Database} label="General" active={step === 1} done={step > 1} />
            <StepItem icon={ShieldCheck} label="Credentials" active={step === 2} done={step > 2} />
            <StepItem icon={Settings2} label="Advanced" active={step === 3} done={step > 3} />
            <StepItem icon={Globe} label="Review" active={step === 4} />
          </div>

          <div className="mt-auto pt-24">
            <div className="p-4 bg-amber-400/5 border border-amber-400/10 rounded-2xl">
              <div className="flex items-center gap-2 text-amber-400 mb-2">
                <Zap size={16} fill="currentColor" />
                <span className="text-xs font-bold uppercase">AI Assistant</span>
              </div>
              <p className="text-[10px] text-gray-400 leading-relaxed">
                QueryBridge AI is analyzing your inputs for security best practices.
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col min-h-[600px]">
          <div className="flex justify-between items-center p-8 border-b border-gray-800/50">
            <h3 className="text-2xl font-bold">Connect Data Source</h3>
            <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full transition-colors text-gray-500">
              <X size={24} />
            </button>
          </div>

          <div className="flex-1 p-10 overflow-y-auto">
            {step === 1 && (
              <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-gray-400">Connection Name</label>
                    <input 
                      className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 focus:border-blue-500 transition-colors"
                      placeholder="e.g. Sales Production"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-gray-400">Database Engine</label>
                    <select className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 focus:border-blue-500 transition-colors appearance-none">
                      <option value="postgres">PostgreSQL</option>
                      <option value="snowflake">Snowflake</option>
                      <option value="mysql">MySQL</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6 pt-4">
                  <div className="col-span-2 space-y-2">
                    <label className="text-sm font-semibold text-gray-400">Host / Endpoint</label>
                    <input 
                      className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 focus:border-blue-500 transition-colors"
                      placeholder="db.example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-gray-400">Port</label>
                    <input 
                      type="number"
                      className="w-full bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 focus:border-blue-500 transition-colors"
                      value={formData.port}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 2-4 content would go here */}
          </div>

          {/* Footer */}
          <div className="p-8 border-t border-gray-800/50 bg-[#141414]/50 flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button 
                onClick={handleTest}
                disabled={isTesting}
                className="flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-white transition-colors disabled:opacity-50"
              >
                {isTesting ? <Loader2 size={16} className="animate-spin" /> : <Activity size={16} />}
                Test Connection
              </button>
              {testResult && (
                <div className={`flex items-center gap-2 text-xs font-bold ${testResult.success ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {testResult.success ? <CheckCircle size={14} /> : <AlertTriangle size={14} />}
                  {testResult.success ? `SUCCESS (${testResult.latency})` : 'FAILED'}
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <button className="px-6 py-2.5 rounded-xl font-bold text-gray-400 hover:bg-gray-800 transition-colors">
                Save Draft
              </button>
              <button 
                onClick={() => setStep(step + 1)}
                className="px-8 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold transition-all shadow-lg shadow-blue-900/20"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

const StepItem = ({ icon: Icon, label, active, done }: any) => (
  <div className={`flex items-center gap-4 transition-colors ${active ? 'text-blue-500' : done ? 'text-emerald-500' : 'text-gray-600'}`}>
    <div className={`p-2 rounded-lg border ${active ? 'border-blue-500/50 bg-blue-500/10' : done ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-gray-800 bg-gray-900'}`}>
      <Icon size={18} />
    </div>
    <span className="font-bold text-sm tracking-wide">{label}</span>
  </div>
);

export default CreateConnectionModal;
