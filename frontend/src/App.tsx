import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';

// Core Pages
import ConnectionDashboard from './pages/connections/ConnectionDashboard';
import SemanticLayer from './pages/semantic/SemanticLayer';
import AgentCenter from './pages/ai/AgentCenter';
import AdminDashboard from './pages/admin/AdminDashboard';
import GovernancePage from './pages/governance/GovernancePage';
import AuditLogsPage from './pages/admin/AuditLogsPage';

// Lazy Loaded Modules
const NotebooksPage = lazy(() => import('./pages/notebooks/NotebooksPage'));
const CatalogPage = lazy(() => import('./pages/catalog/CatalogExplorerPage'));
const TableDetailsPage = lazy(() => import('./pages/catalog/TableDetailsPage'));
const MonitoringPage = lazy(() => import('./pages/monitoring/MonitoringPage'));

// Placeholder for remaining pages
import ModulePlaceholder from './pages/ModulePlaceholder';
import { Activity, GitBranch, Bell, Users, Puzzle, Settings, LineChart, Cpu } from 'lucide-react';

const App: React.FC = () => {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Layout>
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin" />
          </div>
        }>
          <Routes>
            {/* Intelligence */}
            <Route path="/agent-center" element={<AgentCenter />} />
            <Route path="/notebooks" element={<NotebooksPage />} />
            <Route path="/semantic" element={<SemanticLayer />} />

            {/* Analytics */}
            <Route path="/dashboards" element={<AdminDashboard />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/catalog/table/:tableId" element={<TableDetailsPage />} />

            {/* Infrastructure */}
            <Route path="/connections" element={<ConnectionDashboard />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/lineage" element={<ModulePlaceholder title="Data Lineage" icon={GitBranch} />} />

            {/* Governance */}
            <Route path="/governance" element={<GovernancePage />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/audit" element={<AuditLogsPage />} />
            <Route path="/alerts" element={<ModulePlaceholder title="Alert Center" icon={Bell} />} />

            {/* System */}
            <Route path="/settings" element={<ModulePlaceholder title="Platform Settings" icon={Settings} />} />

            {/* Redirects */}
            <Route path="/" element={<Navigate to="/connections" replace />} />
            <Route path="*" element={<Navigate to="/connections" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

export default App;
