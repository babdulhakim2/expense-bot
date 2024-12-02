'use client';

import { 
  Building2Icon, 
  ChevronDownIcon, 
  PlusCircleIcon,
  Settings2Icon,
  BuildingIcon,
  BarChart3Icon
} from "lucide-react";
import { useState } from "react";

type Business = {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'pending' | 'inactive';
  lastSync?: string;
};

const mockBusinesses: Business[] = [
  {
    id: '1',
    name: 'Acme Corp',
    type: 'Retail',
    status: 'active',
    lastSync: '5 mins ago'
  },
  {
    id: '2',
    name: 'Tech Solutions Ltd',
    type: 'Technology',
    status: 'active',
    lastSync: '1 hour ago'
  }
];

export function BusinessSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedBusiness, setSelectedBusiness] = useState(mockBusinesses[0]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 w-full text-left text-sm hover:bg-gray-800 rounded-md"
      >
        <Building2Icon className="h-5 w-5" />
        <div className="flex-1 min-w-0">
          <p className="font-medium">{selectedBusiness.name}</p>
          <p className="text-xs text-gray-400">{selectedBusiness.type}</p>
        </div>
        <ChevronDownIcon className="h-4 w-4 opacity-50" />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 w-full mt-2 py-2 bg-gray-900 rounded-md shadow-lg border border-gray-800">
          <div className="px-2 pb-2 mb-2 border-b border-gray-800">
            <p className="px-2 pb-1.5 text-xs font-medium text-gray-400">
              Switch Business
            </p>
            {mockBusinesses.map((business) => (
              <button
                key={business.id}
                onClick={() => {
                  setSelectedBusiness(business);
                  setIsOpen(false);
                }}
                className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded"
              >
                <BuildingIcon className="h-4 w-4" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{business.name}</p>
                  <p className="text-xs text-gray-400">Last sync: {business.lastSync}</p>
                </div>
                {business.id === selectedBusiness.id && (
                  <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                )}
              </button>
            ))}
          </div>
          
          <div className="px-2">
            <button
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded text-blue-400"
            >
              <PlusCircleIcon className="h-4 w-4" />
              Add Business
            </button>
            <button
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded"
            >
              <Settings2Icon className="h-4 w-4" />
              Business Settings
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 