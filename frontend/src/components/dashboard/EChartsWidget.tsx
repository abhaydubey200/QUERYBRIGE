import React from 'react';

interface EChartsWidgetProps {
  option: any;
  title: string;
  loading?: boolean;
}

const EChartsWidget: React.FC<EChartsWidgetProps> = ({ option, title, loading }) => {
  const points = Array.isArray(option?.series?.[0]?.data) ? option.series[0].data.slice(0, 12) : [];
  const max = Math.max(1, ...points.map((point: number) => Number(point) || 0));

  return (
    <div className="bg-[#0a0a0a] border border-gray-800 rounded-xl p-4 flex flex-col h-full group hover:border-blue-500/50 transition-all shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-300 tracking-tight">{title}</h3>
        {loading && (
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        )}
      </div>
      <div className="flex-1 w-full min-h-[200px] flex items-end gap-2 border-t border-gray-900 pt-4">
        {points.length > 0 ? (
          points.map((point: number, index: number) => (
            <div
              key={`${index}-${point}`}
              className="flex-1 min-w-0 rounded-t bg-blue-500/70"
              style={{ height: `${Math.max(8, (Number(point) / max) * 100)}%` }}
            />
          ))
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-gray-500">
            No chart data
          </div>
        )}
      </div>
    </div>
  );
};

export default EChartsWidget;
