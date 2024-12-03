'use client';

import { 
  MessageSquareIcon, 
  ImageIcon, 
  FileSpreadsheetIcon,
  FolderIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  LoaderIcon
} from "lucide-react";

type Activity = {
  id: string;
  type: 'message' | 'image' | 'spreadsheet' | 'folder';
  status: 'success' | 'processing' | 'failed';
  message: string;
  details: string;
  timestamp: string;
  metadata?: {
    amount?: string;
    category?: string;
    spreadsheet?: string;
    folder?: string;
  };
};

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'image',
    status: 'success',
    message: 'Receipt processed successfully',
    details: 'Grocery shopping at Tesco',
    timestamp: '2 minutes ago',
    metadata: {
      amount: '£45.99',
      category: 'Groceries',
      spreadsheet: 'March 2024 Expenses'
    }
  },
  {
    id: '2',
    type: 'message',
    status: 'processing',
    message: 'Processing transaction message',
    details: 'Monthly rent payment',
    timestamp: 'Just now',
    metadata: {
      amount: '£1,200.00'
    }
  },
  {
    id: '3',
    type: 'spreadsheet',
    status: 'success',
    message: 'New spreadsheet created',
    details: 'Q1 2024 Financial Summary',
    timestamp: '10 minutes ago',
    metadata: {
      folder: 'Financial Reports'
    }
  }
];

const getActivityIcon = (type: Activity['type'], status: Activity['status']) => {
  const baseClass = "h-5 w-5";
  const statusColors = {
    success: 'text-green-600',
    processing: 'text-blue-600',
    failed: 'text-red-600'
  };

  switch (type) {
    case 'message':
      return <MessageSquareIcon className={`${baseClass} ${statusColors[status]}`} />;
    case 'image':
      return <ImageIcon className={`${baseClass} ${statusColors[status]}`} />;
    case 'spreadsheet':
      return <FileSpreadsheetIcon className={`${baseClass} ${statusColors[status]}`} />;
    case 'folder':
      return <FolderIcon className={`${baseClass} ${statusColors[status]}`} />;
  }
};

const getStatusIcon = (status: Activity['status']) => {
  switch (status) {
    case 'success':
      return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    case 'processing':
      return <LoaderIcon className="h-4 w-4 text-blue-600 animate-spin" />;
    case 'failed':
      return <AlertCircleIcon className="h-4 w-4 text-red-600" />;
  }
};

export function ActivityFeed() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-lg font-semibold">Recent AI Activity</h2>
        <p className="text-sm text-gray-500">WhatsApp messages and file changes</p>
      </div>
      <div className="divide-y divide-gray-100">
        {mockActivities.map((activity) => (
          <div key={activity.id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-start gap-4">
              <div className={`p-2 rounded-lg ${
                activity.status === 'success' ? 'bg-green-50' :
                activity.status === 'processing' ? 'bg-blue-50' :
                'bg-red-50'
              }`}>
                {getActivityIcon(activity.type, activity.status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{activity.message}</span>
                  {getStatusIcon(activity.status)}
                </div>
                <p className="text-sm text-gray-600 mt-1">{activity.details}</p>
                {activity.metadata && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {activity.metadata.amount && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 text-xs font-medium text-gray-600">
                        {activity.metadata.amount}
                      </span>
                    )}
                    {activity.metadata.category && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-50 text-xs font-medium text-blue-700">
                        {activity.metadata.category}
                      </span>
                    )}
                    {activity.metadata.spreadsheet && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-green-50 text-xs font-medium text-green-700">
                        📊 {activity.metadata.spreadsheet}
                      </span>
                    )}
                    {activity.metadata.folder && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-yellow-50 text-xs font-medium text-yellow-700">
                        📁 {activity.metadata.folder}
                      </span>
                    )}
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-2">{activity.timestamp}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 