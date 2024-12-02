'use client';

import { 
  BotIcon, 
  PauseCircleIcon, 
  PlayCircleIcon, 
  XCircleIcon,
  AlertTriangleIcon,
  CheckCircle2Icon,
  MessageSquareIcon,
  Settings2Icon
} from "lucide-react";
import { useState } from "react";

type AIStatus = 'active' | 'paused' | 'processing' | 'error';

type AIAction = {
  id: string;
  type: 'categorize' | 'create_folder' | 'update_spreadsheet' | 'analyze';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  description: string;
  progress?: number;
  canCancel?: boolean;
};

const mockPendingActions: AIAction[] = [
  {
    id: 'action1',
    type: 'categorize',
    status: 'in_progress',
    description: 'Categorizing recent transactions',
    progress: 45,
    canCancel: true
  },
  {
    id: 'action2',
    type: 'create_folder',
    status: 'pending',
    description: 'Creating "Tax Documents 2024" folder',
    canCancel: true
  }
];

export function AICommandCenter() {
  const [aiStatus, setAIStatus] = useState<AIStatus>('active');
  const [pendingActions, setPendingActions] = useState<AIAction[]>(mockPendingActions);

  const toggleAIStatus = () => {
    setAIStatus(aiStatus === 'active' ? 'paused' : 'active');
  };

  const cancelAction = (actionId: string) => {
    setPendingActions(actions => actions.filter(a => a.id !== actionId));
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-full ${
              aiStatus === 'active' ? 'bg-green-50' :
              aiStatus === 'paused' ? 'bg-yellow-50' :
              aiStatus === 'error' ? 'bg-red-50' :
              'bg-blue-50'
            }`}>
              <BotIcon className={`h-6 w-6 ${
                aiStatus === 'active' ? 'text-green-600' :
                aiStatus === 'paused' ? 'text-yellow-600' :
                aiStatus === 'error' ? 'text-red-600' :
                'text-blue-600'
              }`} />
            </div>
            <div>
              <h2 className="text-lg font-semibold">AI Assistant</h2>
              <p className="text-sm text-gray-500">
                {aiStatus === 'active' ? 'Actively monitoring WhatsApp' :
                 aiStatus === 'paused' ? 'Assistant paused' :
                 aiStatus === 'error' ? 'Error detected' :
                 'Processing messages'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={toggleAIStatus}
              className={`p-2 rounded-full hover:bg-gray-100 ${
                aiStatus === 'paused' ? 'text-yellow-600' : 'text-gray-600'
              }`}
            >
              {aiStatus === 'active' ? 
                <PauseCircleIcon className="h-5 w-5" /> : 
                <PlayCircleIcon className="h-5 w-5" />
              }
            </button>
            <button className="p-2 rounded-full hover:bg-gray-100">
              <Settings2Icon className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-4 flex gap-2">
          <button className="inline-flex items-center px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 text-sm hover:bg-blue-100">
            <MessageSquareIcon className="h-4 w-4 mr-1.5" />
            Send Command
          </button>
          <button className="inline-flex items-center px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm hover:bg-gray-200">
            View History
          </button>
        </div>
      </div>

      {/* Pending Actions */}
      <div className="p-4 space-y-3">
        {pendingActions.map((action) => (
          <div 
            key={action.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex items-center gap-3 flex-1">
              <div className={`p-1.5 rounded-full ${
                action.status === 'in_progress' ? 'bg-blue-100' :
                action.status === 'completed' ? 'bg-green-100' :
                action.status === 'failed' ? 'bg-red-100' :
                'bg-gray-100'
              }`}>
                {action.status === 'in_progress' ? (
                  <div className="h-3 w-3 rounded-full bg-blue-500 animate-pulse" />
                ) : action.status === 'completed' ? (
                  <CheckCircle2Icon className="h-3 w-3 text-green-600" />
                ) : action.status === 'failed' ? (
                  <AlertTriangleIcon className="h-3 w-3 text-red-600" />
                ) : (
                  <div className="h-3 w-3 rounded-full bg-gray-400" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">{action.description}</p>
                {action.progress !== undefined && (
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                    <div 
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${action.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
            {action.canCancel && (
              <button 
                onClick={() => cancelAction(action.id)}
                className="p-1 hover:bg-gray-200 rounded-full ml-2"
              >
                <XCircleIcon className="h-4 w-4 text-gray-500" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 