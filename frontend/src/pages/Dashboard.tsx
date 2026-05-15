import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Users, DollarSign } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Jan', value: 400 },
  { name: 'Feb', value: 300 },
  { name: 'Mar', value: 600 },
  { name: 'Apr', value: 800 },
  { name: 'May', value: 500 },
  { name: 'Jun', value: 900 },
];

const Dashboard: React.FC = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-white mb-2">Executive Overview</h1>
        <p className="text-gray-400">Real-time performance metrics across all connectors.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
        {[
          { label: 'Revenue', value: '$2.4M', icon: DollarSign, color: 'text-green-500' },
          { label: 'Active Users', value: '12.5k', icon: Users, color: 'text-blue-500' },
          { label: 'Conversion', value: '3.2%', icon: TrendingUp, color: 'text-purple-500' },
          { label: 'Queries', value: '1.2k', icon: BarChart3, color: 'text-orange-500' },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-[#111] border border-white/10 p-6 rounded-2xl"
          >
            <div className={`w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center mb-4 ${stat.color}`}>
              <stat.icon size={20} />
            </div>
            <p className="text-gray-500 text-sm">{stat.label}</p>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      <div className="bg-[#111] border border-white/10 p-8 rounded-2xl h-[400px]">
        <h3 className="text-lg font-semibold text-white mb-8">Growth Trajectory</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#222" />
            <XAxis dataKey="name" stroke="#555" />
            <YAxis stroke="#555" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }}
              itemStyle={{ color: '#fff' }}
            />
            <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={{ r: 6, fill: '#3b82f6' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Dashboard;
