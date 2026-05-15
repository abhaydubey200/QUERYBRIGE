import { 
  LayoutDashboard, 
  Database, 
  Network, 
  ShieldCheck, 
  Settings, 
  Cpu, 
  BookOpen, 
  Search, 
  Activity, 
  GitBranch, 
  Bell, 
  Users, 
  Puzzle, 
  Lock,
  LineChart,
  Terminal,
  Zap
} from 'lucide-react';

export const navigationItems = [
  {
    category: 'Intelligence',
    items: [
      { icon: Zap, label: 'Agent Center', path: '/agent-center', badge: 'AI' },
      { icon: Terminal, label: 'Notebooks', path: '/notebooks' },
      { icon: Network, label: 'Semantic Layer', path: '/semantic' },
      { icon: Cpu, label: 'AI Labs', path: '/ai' },
    ]
  },
  {
    category: 'Analytics',
    items: [
      { icon: LayoutDashboard, label: 'Dashboards', path: '/dashboards' },
      { icon: Search, label: 'Data Catalog', path: '/catalog' },
      { icon: LineChart, label: 'Metrics', path: '/metrics' },
    ]
  },
  {
    category: 'Infrastructure',
    items: [
      { icon: Database, label: 'Connections', path: '/connections' },
      { icon: Activity, label: 'Monitoring', path: '/monitoring' },
      { icon: GitBranch, label: 'Data Lineage', path: '/lineage' },
    ]
  },
  {
    category: 'Governance',
    items: [
      { icon: ShieldCheck, label: 'Policy Engine', path: '/governance' },
      { icon: Lock, label: 'Access Control', path: '/admin' },
      { icon: BookOpen, label: 'Audit Logs', path: '/audit' },
      { icon: Bell, label: 'Alerts', path: '/alerts' },
    ]
  },
  {
    category: 'System',
    items: [
      { icon: Users, label: 'Workspaces', path: '/workspace' },
      { icon: Puzzle, label: 'Plugins', path: '/plugins' },
      { icon: Settings, label: 'Platform Settings', path: '/settings' },
    ]
  }
];
