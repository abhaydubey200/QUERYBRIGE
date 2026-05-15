import React from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-[#050505] text-gray-200">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 relative overflow-y-auto">
          {/* Ambient background effects */}
          <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-blue-600/5 blur-[120px] pointer-events-none rounded-full -mr-64 -mt-64" />
          <div className="fixed bottom-0 left-0 w-[500px] h-[500px] bg-indigo-600/5 blur-[120px] pointer-events-none rounded-full -ml-64 -mb-64" />
          
          <div className="relative z-10 p-8 max-w-[1600px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
