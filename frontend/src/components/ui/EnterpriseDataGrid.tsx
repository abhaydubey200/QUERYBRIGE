import React, { useState, useMemo } from 'react';
import { cn } from "@/lib/utils";
import { Download, Filter, ArrowUpDown, MoreHorizontal, Settings2 } from 'lucide-react';
import { Button } from "@/components/ui/button";

interface Column {
  key: string;
  label: string;
  width?: number;
  type?: 'string' | 'number' | 'date' | 'boolean';
}

interface EnterpriseDataGridProps {
  columns: Column[];
  data: any[];
  isLoading?: boolean;
  onSort?: (key: string) => void;
}

const EnterpriseDataGrid: React.FC<EnterpriseDataGridProps> = ({ 
  columns, 
  data, 
  isLoading,
  onSort 
}) => {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  // Virtualization logic would go here for multi-million row support
  // For now, we implement a highly optimized grid with sticky headers and premium styling

  return (
    <div className="flex flex-col h-full bg-[#080808] border border-white/5 rounded-xl overflow-hidden shadow-2xl">
      {/* Grid Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
            {data.length} Rows
          </span>
          <div className="h-4 w-px bg-white/10 mx-2" />
          <Button variant="ghost" size="sm" className="h-7 text-[10px] uppercase tracking-wider text-gray-400 hover:text-white">
            <Filter size={12} className="mr-2" /> Filter
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-[10px] uppercase tracking-wider text-gray-400 hover:text-white">
            <ArrowUpDown size={12} className="mr-2" /> Sort
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-white">
            <Download size={14} />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-white">
            <Settings2 size={14} />
          </Button>
        </div>
      </div>

      {/* Grid Body */}
      <div className="flex-1 overflow-auto custom-scrollbar relative">
        <table className="w-full border-collapse text-xs font-mono">
          <thead className="sticky top-0 z-10">
            <tr className="bg-[#0a0a0a]">
              <th className="w-10 p-2 border-r border-b border-white/5 text-gray-600">#</th>
              {columns.map(col => (
                <th 
                  key={col.key}
                  className="px-4 py-3 text-left border-r border-b border-white/5 text-gray-400 font-medium hover:bg-white/5 cursor-pointer transition-colors"
                  style={{ width: col.width }}
                  onClick={() => onSort?.(col.key)}
                >
                  <div className="flex items-center justify-between">
                    <span>{col.label}</span>
                    <MoreHorizontal size={12} className="opacity-0 group-hover:opacity-100" />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="p-2 border-r border-white/5 bg-white/[0.01]" />
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 border-r border-white/5">
                      <div className="h-3 bg-white/5 rounded w-full" />
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              data.map((row, rowIndex) => (
                <tr 
                  key={rowIndex}
                  onMouseEnter={() => setHoveredRow(rowIndex)}
                  onMouseLeave={() => setHoveredRow(null)}
                  className={cn(
                    "border-b border-white/5 transition-colors",
                    hoveredRow === rowIndex ? "bg-blue-500/5" : "bg-transparent"
                  )}
                >
                  <td className="p-2 border-r border-white/5 text-center text-gray-600 bg-black/20">
                    {rowIndex + 1}
                  </td>
                  {columns.map(col => (
                    <td 
                      key={col.key} 
                      className={cn(
                        "px-4 py-2 border-r border-white/5 truncate max-w-[300px]",
                        col.type === 'number' ? "text-blue-400 text-right" : "text-gray-300"
                      )}
                    >
                      {String(row[col.key] ?? '')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EnterpriseDataGrid;
