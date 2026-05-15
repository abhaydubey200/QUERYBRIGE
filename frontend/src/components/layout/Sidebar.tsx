import React from 'react';
import { NavLink } from 'react-router-dom';
import { LogOut, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { navigationItems } from '../../navigation/navigationItems';

const NavItem = ({ item }: { item: any }) => (
  <NavLink
    to={item.path}
    className={({ isActive }) => `
      flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 group relative
      ${isActive 
        ? 'bg-blue-600/10 text-blue-400' 
        : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
      }
    `}
  >
    {({ isActive }: { isActive: boolean }) => (
      <>
        <item.icon 
          size={18} 
          strokeWidth={isActive ? 2.5 : 2} 
          className={isActive ? 'text-blue-400' : 'text-gray-400 group-hover:text-gray-200'}
        />
        <span className="font-medium text-sm">{item.label}</span>
        
        {item.badge && (
          <span className="ml-auto text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-bold border border-blue-500/20">
            {item.badge}
          </span>
        )}
        
        {isActive && (
          <motion.div 
            layoutId="active-nav"
            className="absolute left-0 w-1 h-6 bg-blue-500 rounded-r-full shadow-[0_0_15px_rgba(59,130,246,0.5)]"
          />
        )}
      </>
    )}
  </NavLink>
);

const Sidebar = () => {
  return (
    <div className="w-72 bg-[#0a0a0a] border-r border-white/5 flex flex-col h-screen sticky top-0 overflow-hidden">
      {/* Brand Section */}
      <div className="p-6">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
            <div className="relative w-10 h-10 bg-[#111] rounded-xl flex items-center justify-center border border-white/10 shadow-2xl">
              <div className="w-6 h-6 bg-blue-600 rounded-[4px] flex items-center justify-center">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              </div>
            </div>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-none">QueryBridge</h1>
            <p className="text-[10px] text-blue-500 font-bold uppercase tracking-widest mt-1">Enterprise OS</p>
          </div>
        </div>

        {/* Navigation Groups */}
        <div className="space-y-8 overflow-y-auto max-h-[calc(100vh-320px)] scrollbar-hide pr-2">
          {navigationItems.map((group) => (
            <div key={group.category}>
              <h2 className="px-4 text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-3">
                {group.category}
              </h2>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavItem key={item.path} item={item} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Section */}
      <div className="mt-auto p-6 bg-gradient-to-t from-[#050505] to-transparent border-t border-white/5">
        <div className="p-4 bg-white/5 rounded-2xl border border-white/5 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10 flex items-center justify-center text-xs font-bold text-white">
              AD
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-white truncate">Abhay Dubey</p>
              <p className="text-[10px] text-gray-500 truncate">System Architect</p>
            </div>
          </div>
        </div>

        <button className="flex items-center justify-between w-full px-4 py-3 text-gray-400 hover:text-rose-400 hover:bg-rose-500/5 rounded-xl transition-all group border border-transparent hover:border-rose-500/20">
          <div className="flex items-center gap-3">
            <LogOut size={18} />
            <span className="font-semibold text-sm">Exit Runtime</span>
          </div>
          <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 transition-all" />
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
