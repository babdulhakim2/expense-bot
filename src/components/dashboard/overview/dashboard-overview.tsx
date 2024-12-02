'use client';

import { 
  MessageSquareIcon, 
  FileSpreadsheetIcon,
  FolderIcon,
  BarChart3Icon,
  ArrowUpIcon,
  ArrowDownIcon
} from "lucide-react";
import { ActivityFeed } from './activity-feed';
import { AICommandCenter } from '../ai/ai-command-center';

const mockStats = [
  { 
    label: 'Processed Messages', 
    value: '1,234', 
    icon: MessageSquareIcon,
    change: '+28%',
    trend: 'up'
  },
  { 
    label: 'Active Spreadsheets', 
    value: '156', 
    icon: FileSpreadsheetIcon,
    change: '+8%',
    trend: 'up'
  },
  { 
    label: 'Total Folders', 
    value: '24', 
    icon: FolderIcon,
    change: '+12%',
    trend: 'up'
  },
  { 
    label: 'Transactions', 
    value: '2.4k', 
    icon: BarChart3Icon,
    change: '+15%',
    trend: 'up'
  }
];

export function DashboardOverview() {
  return (
    <div className="p-6 space-y-6">
      {/* AI Command Center */}
      <AICommandCenter />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {mockStats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <h3 className="text-2xl font-semibold mt-1">{stat.value}</h3>
              </div>
              <div className="h-12 w-12 bg-blue-50 rounded-full flex items-center justify-center">
                <stat.icon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center">
              {stat.trend === 'up' ? (
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
              ) : (
                <ArrowDownIcon className="h-4 w-4 text-red-500" />
              )}
              <span className={`ml-1 text-sm ${
                stat.trend === 'up' ? 'text-green-500' : 'text-red-500'
              }`}>
                {stat.change}
              </span>
              <span className="ml-2 text-sm text-gray-500">vs last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Feed */}
      <ActivityFeed />
    </div>
  );
} 