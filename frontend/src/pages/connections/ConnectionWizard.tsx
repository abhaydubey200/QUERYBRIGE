import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Database,
  Shield,
  Activity,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Plus,
  Server,
  Snowflake,
  KeyRound,
  FileSpreadsheet,
  FileText,
  Upload,
} from 'lucide-react';

interface ConnectionWizardProps {
  onClose: () => void;
  onSuccess: () => void;
}

type DbType = 'postgres' | 'mysql' | 'mssql' | 'oracle' | 'snowflake' | 'csv' | 'excel';

interface ConnectionForm {
  db_type: DbType;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode: string;
  schema_name: string;
  warehouse: string;
  role: string;
  auth_type: string;
  service_name: string;
  sid: string;
  authenticator: string;
  metadata_limit: number;
  charset: string;
  ssl_ca: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const DB_TYPES: Array<{ id: DbType; name: string; icon: React.ElementType; port: number }> = [
  { id: 'postgres', name: 'PostgreSQL', icon: Database, port: 5432 },
  { id: 'mysql', name: 'MySQL', icon: Server, port: 3306 },
  { id: 'mssql', name: 'SQL Server', icon: Database, port: 1433 },
  { id: 'oracle', name: 'Oracle', icon: Database, port: 1521 },
  { id: 'snowflake', name: 'Snowflake', icon: Snowflake, port: 443 },
  { id: 'csv', name: 'CSV File', icon: FileText, port: 0 },
  { id: 'excel', name: 'Excel Sheet', icon: FileSpreadsheet, port: 0 },
];

const initialForm: ConnectionForm = {
  db_type: 'postgres',
  name: '',
  host: '',
  port: 5432,
  database: '',
  username: '',
  password: '',
  ssl_mode: 'prefer',
  schema_name: '',
  warehouse: '',
  role: '',
  auth_type: 'sql',
  service_name: '',
  sid: '',
  authenticator: '',
  metadata_limit: 1000,
  charset: 'utf8mb4',
  ssl_ca: '',
};

const ConnectionWizard = ({ onClose, onSuccess }: ConnectionWizardProps) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<ConnectionForm>(initialForm);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<any>(null);

  const selectedDb = useMemo(() => DB_TYPES.find((type) => type.id === formData.db_type) || DB_TYPES[0], [formData.db_type]);
  const isSnowflake = formData.db_type === 'snowflake';
  const isOracle = formData.db_type === 'oracle';
  const isMssql = formData.db_type === 'mssql';
  const isMysql = formData.db_type === 'mysql';
  const isFile = formData.db_type === 'csv' || formData.db_type === 'excel';

  const updateField = <K extends keyof ConnectionForm>(key: K, value: ConnectionForm[K]) => {
    setFormData((current) => ({ ...current, [key]: value }));
    setTestResult(null);
    setSaveError(null);
  };

  const selectDbType = (dbType: DbType) => {
    const selected = DB_TYPES.find((type) => type.id === dbType) || DB_TYPES[0];
    setFormData((current) => ({
      ...current,
      db_type: dbType,
      port: selected.port,
      ssl_mode: dbType === 'snowflake' ? 'verify-full' : 'prefer',
      auth_type: dbType === 'mssql' ? 'sql' : current.auth_type,
    }));
    setStep(2);
  };
  
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setSaveError(null);
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);
    try {
      const response = await fetch(`${API_URL}/storage/upload`, { method: 'POST', body: uploadFormData });
      const data = await response.json();
      if (response.ok) {
        setUploadedFile(data);
        setFormData(current => ({ ...current, host: data.file_path, name: current.name || file.name.split('.')[0] }));
      } else {
        setSaveError(data.detail || 'Upload failed');
      }
    } catch {
      setSaveError('Failed to connect to storage service');
    } finally {
      setUploading(false);
    }
  };

  const buildPayload = () => ({
    db_type: formData.db_type,
    name: formData.name.trim(),
    host: formData.host.trim(),
    port: Number(formData.port),
    database: formData.database.trim() || undefined,
    username: formData.username.trim() || '',
    password: formData.password || '',
    ssl_mode: formData.ssl_mode,
    schema_name: formData.schema_name.trim() || undefined,
    warehouse: formData.warehouse.trim() || undefined,
    role: formData.role.trim() || undefined,
    auth_type: formData.auth_type || undefined,
    service_name: formData.service_name.trim() || undefined,
    sid: formData.sid.trim() || undefined,
    authenticator: formData.authenticator || undefined,
    charset: formData.charset || undefined,
    ssl_ca: formData.ssl_ca.trim() || undefined,
    metadata_limit: formData.metadata_limit,
    advanced_settings: {},
  });

  const canContinue = step !== 2 || Boolean(formData.name && formData.host);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    setSaveError(null);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000);
      const response = await fetch(`${API_URL}/connections/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload()),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const result = await response.json();
      if (!response.ok || !result.success) {
        const err = result.error || {};
        setTestResult({
          success: false,
          error: err.message || 'Connection test failed',
          diagnostics: {
            ...(err.details || {}),
            'Trace ID': err.trace_id || 'N/A',
          },
        });
      } else {
        setTestResult({ success: true, ...result.data });
      }
    } catch (err: any) {
      const msg = err.name === 'AbortError'
        ? 'Connection test timed out (45s). Check host/port.'
        : 'Cannot reach QueryBridge API. Ensure the backend is running.';
      setTestResult({
        success: false,
        error: msg,
        diagnostics: { 'Network': 'Failed', 'Hint': 'Check that port 8000 is accessible' },
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);
      const response = await fetch(`${API_URL}/connections/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload()),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.error?.message || 'Connection save failed');
      }
      onSuccess();
      onClose();
    } catch (error: any) {
      const msg = error.name === 'AbortError'
        ? 'Save timed out. Backend may be overloaded.'
        : error.message || 'Connection save failed';
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="bg-[#121212] border border-gray-800 w-full max-w-4xl h-[82vh] rounded-2xl overflow-hidden flex flex-col shadow-2xl"
      >
        <div className="p-6 border-b border-gray-800 flex justify-between items-center bg-[#1a1a1a]">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Plus size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold">New Data Connection</h2>
              <p className="text-sm text-gray-500">Step {step} of 4</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full transition-colors" aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-8">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {DB_TYPES.map((type) => {
                  const Icon = type.icon;
                  return (
                    <button key={type.id} onClick={() => selectDbType(type.id)}
                      className={`p-5 rounded-xl border transition-all flex items-center gap-4 text-left ${formData.db_type === type.id ? 'border-blue-600 bg-blue-600/10' : 'border-gray-800 bg-gray-900/50 hover:border-gray-700'}`}>
                      <Icon size={24} className="text-blue-400" />
                      <div>
                        <h3 className="font-bold">{type.name}</h3>
                        <p className="text-xs text-gray-500">{type.port ? `Port ${type.port}` : 'File-based'}</p>
                      </div>
                    </button>
                  );
                })}
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-2xl mx-auto w-full space-y-5">
                <SectionTitle icon={selectedDb.icon} title={`${selectedDb.name} Endpoint`} />
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Connection Name" className="col-span-2">
                    <input className="field" placeholder="e.g. Sales Data" value={formData.name} onChange={(e) => updateField('name', e.target.value)} />
                  </Field>
                  <Field label={isFile ? 'Full File Path' : isSnowflake ? 'Account Identifier' : 'Host'} className="col-span-2">
                    <input className="field" placeholder={isFile ? 'c:/path/to/data.csv' : 'localhost'} value={formData.host} onChange={(e) => updateField('host', e.target.value)} />
                  </Field>
                  {isFile && (
                    <div className="col-span-2">
                      <div className={`p-8 border-2 border-dashed rounded-xl transition-all flex flex-col items-center justify-center gap-4 ${uploadedFile ? 'border-emerald-500 bg-emerald-500/5' : 'border-gray-800 bg-gray-900/50 hover:border-blue-500/50'}`}>
                        <input type="file" id="file-upload" className="hidden" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} disabled={uploading} />
                        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                          <div className={`p-4 rounded-full ${uploadedFile ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>
                            {uploading ? <Loader2 className="animate-spin" size={32} /> : <Upload size={32} />}
                          </div>
                          <div className="text-center">
                            <p className="font-bold">{uploadedFile ? 'File Uploaded Successfully' : 'Click to Upload Source File'}</p>
                            <p className="text-sm text-gray-500">{uploadedFile ? uploadedFile.filename : 'CSV and Excel formats'}</p>
                          </div>
                        </label>
                      </div>
                    </div>
                  )}
                  {!isFile && (
                    <>
                      <Field label="Port">
                        <input className="field" type="number" value={formData.port} onChange={(e) => updateField('port', Number(e.target.value) || selectedDb.port)} />
                      </Field>
                      <Field label={isOracle ? 'Service / PDB' : 'Database'} className="col-span-2">
                        <input className="field" value={formData.database} onChange={(e) => updateField('database', e.target.value)} />
                      </Field>
                      <Field label="Username">
                        <input className="field" value={formData.username} onChange={(e) => updateField('username', e.target.value)} />
                      </Field>
                      <Field label="Password">
                        <input className="field" type="password" value={formData.password} onChange={(e) => updateField('password', e.target.value)} />
                      </Field>
                    </>
                  )}
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-2xl mx-auto w-full space-y-6">
                <SectionTitle icon={Shield} title="Security And Driver Settings" />
                <div className="grid grid-cols-2 gap-4">
                  <Field label="SSL Mode">
                    <select className="field" value={formData.ssl_mode} onChange={(e) => updateField('ssl_mode', e.target.value)}>
                      <option value="disable">Disable</option>
                      <option value="prefer">Prefer</option>
                      <option value="require">Require</option>
                      <option value="verify-ca">Verify CA</option>
                      <option value="verify-full">Verify Full</option>
                    </select>
                  </Field>
                  <Field label="Metadata Limit">
                    <input className="field" type="number" min={1} max={10000} value={formData.metadata_limit} onChange={(e) => updateField('metadata_limit', Number(e.target.value) || 1000)} />
                  </Field>
                  <Field label="Default Schema">
                    <input className="field" value={formData.schema_name} onChange={(e) => updateField('schema_name', e.target.value)} />
                  </Field>
                  {isMysql && (
                    <Field label="Charset">
                      <input className="field" value={formData.charset} onChange={(e) => updateField('charset', e.target.value)} />
                    </Field>
                  )}
                  {isMssql && (
                    <Field label="Authentication">
                      <select className="field" value={formData.auth_type} onChange={(e) => updateField('auth_type', e.target.value)}>
                        <option value="sql">SQL Auth</option>
                        <option value="windows">Windows Auth</option>
                      </select>
                    </Field>
                  )}
                  {isOracle && (
                    <>
                      <Field label="SID">
                        <input className="field" value={formData.sid} onChange={(e) => updateField('sid', e.target.value)} />
                      </Field>
                      <Field label="Service Name">
                        <input className="field" value={formData.service_name} onChange={(e) => updateField('service_name', e.target.value)} />
                      </Field>
                    </>
                  )}
                  {isSnowflake && (
                    <>
                      <Field label="Warehouse">
                        <input className="field" value={formData.warehouse} onChange={(e) => updateField('warehouse', e.target.value)} />
                      </Field>
                      <Field label="Role">
                        <input className="field" value={formData.role} onChange={(e) => updateField('role', e.target.value)} />
                      </Field>
                      <Field label="Authenticator">
                        <select className="field" value={formData.authenticator} onChange={(e) => updateField('authenticator', e.target.value)}>
                          <option value="">Password</option>
                          <option value="externalbrowser">External Browser</option>
                        </select>
                      </Field>
                    </>
                  )}
                  <Field label="CA Certificate" className="col-span-2">
                    <textarea className="field min-h-[96px] resize-y" value={formData.ssl_ca} onChange={(e) => updateField('ssl_ca', e.target.value)} />
                  </Field>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="max-w-2xl mx-auto w-full space-y-6">
                <SectionTitle icon={Activity} title="Connection Diagnostics" />
                <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl p-6">
                  <div className="flex items-center justify-between gap-4 mb-6">
                    <div className="min-w-0">
                      <h3 className="font-bold truncate">{formData.name || selectedDb.name}</h3>
                      <p className="text-sm text-gray-500 truncate">{formData.host}{formData.port ? `:${formData.port}` : ''}</p>
                    </div>
                    <button onClick={handleTest} disabled={testing || !canContinue} className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-lg font-bold disabled:opacity-50 flex items-center gap-2 shrink-0">
                      {testing ? <Loader2 className="animate-spin" size={18} /> : <Activity size={18} />}
                      Run Test
                    </button>
                  </div>

                  <div className="space-y-3">
                    {testResult?.diagnostics ? (
                      Object.entries(testResult.diagnostics).map(([key, value]) => (
                        <DiagnosticItem key={key} label={formatLabel(key)} value={value} success={testResult.success || !String(value).toLowerCase().includes('failed')} />
                      ))
                    ) : (
                      <>
                        <DiagnosticItem label="Payload Validation" value="Ready" success />
                        <DiagnosticItem label="Driver Probe" value={testing ? 'Running...' : 'Pending'} success={false} pending={!testing} />
                      </>
                    )}

                    {testResult && !testResult.success && (
                      <StatusPanel tone="error" title="Connection Failed" message={testResult.error || 'Check credentials, network, and driver settings.'} />
                    )}
                    {testResult?.success && (
                      <StatusPanel tone="success" title="Connection Verified" message={`Latency ${Number(testResult.latency_ms || 0).toFixed(2)}ms | ${testResult.version || 'Server OK'}`} />
                    )}
                    {saveError && <StatusPanel tone="error" title="Save Failed" message={saveError} />}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-6 border-t border-gray-800 bg-[#1a1a1a] flex justify-between">
          <button onClick={() => setStep((current) => Math.max(1, current - 1))} disabled={step === 1} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors disabled:opacity-0">
            <ChevronLeft size={20} />
            Back
          </button>

          {step < 4 ? (
            <button onClick={() => setStep((current) => current + 1)} disabled={!canContinue} className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-lg font-bold flex items-center gap-2 disabled:opacity-50">
              Continue
              <ChevronRight size={20} />
            </button>
          ) : (
            <button onClick={handleSave} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700 px-8 py-3 rounded-lg font-bold disabled:opacity-50 flex items-center gap-2">
              {saving && <Loader2 className="animate-spin" size={18} />}
              Complete Setup
            </button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

const SectionTitle = ({ icon: Icon, title }: { icon: React.ElementType; title: string }) => (
  <div className="flex items-center gap-3">
    <div className="p-2 rounded-lg bg-blue-600/10 text-blue-400"><Icon size={18} /></div>
    <h3 className="text-lg font-bold">{title}</h3>
  </div>
);

const Field = ({ label, children, className = '' }: { label: string; children: React.ReactNode; className?: string }) => (
  <label className={`space-y-2 ${className}`}>
    <span className="text-sm font-medium text-gray-400">{label}</span>
    {children}
  </label>
);

const DiagnosticItem = ({ label, value, success, pending = false }: { label: string; value: any; success: boolean; pending?: boolean }) => (
  <div className="flex items-center justify-between gap-3 p-3 bg-gray-900/50 rounded-lg border border-gray-800">
    <span className="text-sm font-medium text-gray-300">{label}</span>
    <div className="flex items-center gap-2 min-w-0">
      <span className="text-xs text-gray-500 truncate max-w-[260px]">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
      {pending ? <KeyRound className="text-gray-500" size={16} /> : success ? <CheckCircle2 className="text-emerald-500 shrink-0" size={18} /> : <AlertCircle className="text-amber-500 shrink-0" size={18} />}
    </div>
  </div>
);

const StatusPanel = ({ tone, title, message }: { tone: 'success' | 'error'; title: string; message: string }) => (
  <div className={`mt-4 p-4 rounded-lg flex gap-3 border ${tone === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
    {tone === 'success' ? <CheckCircle2 className="shrink-0" size={20} /> : <AlertCircle className="shrink-0" size={20} />}
    <div>
      <p className="font-bold text-sm uppercase tracking-wider">{title}</p>
      <p className="text-sm opacity-90 break-words">{message}</p>
    </div>
  </div>
);

const formatLabel = (key: string) => key.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

export default ConnectionWizard;
