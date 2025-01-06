'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { BusinessService } from '@/lib/firebase/services/business-service';
import { 
  FileSpreadsheetIcon, 
  FolderIcon, 
  MoreVerticalIcon, 
  PlusIcon, 
  SearchIcon, 
  ChevronRightIcon,
  CalendarIcon,
  ReceiptIcon,
  FolderOpenIcon,
  ExternalLinkIcon,
  ArrowUpDownIcon
} from "lucide-react";
import { format } from 'date-fns';
import { collection, getDocs } from 'firebase/firestore';

interface FolderItem {
  id: string;
  name: string;
  type: string;
  url: string;
  drive_folder_id: string;
  createdAt: Date;
  updatedAt: Date;
}

interface SpreadsheetItem {
  id: string;
  name: string;
  url: string;
  drive_spreadsheet_id: string;
  month: string;
  year: string;
  createdAt: Date;
  updatedAt: Date;
}

export default function FoldersPage() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [spreadsheets, setSpreadsheets] = useState<SpreadsheetItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'folders' | 'spreadsheets'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'updated'>('updated');

  useEffect(() => {
    async function loadBusinessData() {
      try {
        if (session?.user?.email) {
          const business = await BusinessService.getBusinessByUserEmail(session.user.email);
          
          if (business) {
            console.log('Business found:', business);
            
            const [folders, spreadsheets, actions] = await Promise.all([
              BusinessService.getBusinessFolders(business.id),
              BusinessService.getBusinessSpreadsheets(business.id),
              BusinessService.getBusinessActions(business.id)
            ]);

            console.log('Business Folders:', folders);
            console.log('Business Spreadsheets:', spreadsheets);
            console.log('Business Actions:', actions);
            
            setFolders(folders);
            setSpreadsheets(spreadsheets as any);
          }
        }
      } catch (err) {
        console.error('Error loading business data:', err);
        setError('Failed to load business data');
      } finally {
        setLoading(false);
      }
    }

    loadBusinessData();
  }, [session]);

  const organizedFolders = folders.reduce((acc, folder) => {
    if (folder.type === 'business_root') {
      if (!acc.root) acc.root = [];
      acc.root.push(folder);
    } else if (folder.type === 'receipt_root') {
      if (!acc.receipts) acc.receipts = [];
      acc.receipts.push(folder);
    } else if (folder.type === 'transactions') {
      if (!acc.transactions) acc.transactions = [];
      acc.transactions.push(folder);
    }
    return acc;
  }, {} as Record<string, FolderItem[]>);

  const filteredItems = [...folders, ...spreadsheets].filter(item => {
    if (searchTerm && !item.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (filterType === 'folders' && 'drive_spreadsheet_id' in item) {
      return false;
    }
    if (filterType === 'spreadsheets' && !('drive_spreadsheet_id' in item)) {
      return false;
    }
    return true;
  });

  const sortedItems = [...filteredItems].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    }
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Documents</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your financial documents and spreadsheets</p>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setSortBy(sortBy === 'name' ? 'updated' : 'name')}
              className="flex items-center gap-2 px-3 py-2 bg-white text-gray-700 rounded-md border hover:bg-gray-50"
            >
              <ArrowUpDownIcon className="h-4 w-4" />
              Sort by {sortBy === 'name' ? 'Name' : 'Last Updated'}
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              <PlusIcon className="h-4 w-4" />
              New Folder
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search documents..."
              className="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select 
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as any)}
            className="px-3 py-2 bg-white border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Items</option>
            <option value="folders">Folders Only</option>
            <option value="spreadsheets">Spreadsheets Only</option>
          </select>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sortedItems.map((item) => {
            const isSpreadsheet = 'drive_spreadsheet_id' in item;
            
            return (
              <a
                key={item.id}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {isSpreadsheet ? (
                      <div className="p-2 bg-green-50 rounded-lg">
                        <FileSpreadsheetIcon className="h-6 w-6 text-green-600" />
                      </div>
                    ) : (
                      <div className="p-2 bg-blue-50 rounded-lg">
                        {item.type.includes('receipt') ? (
                          <ReceiptIcon className="h-6 w-6 text-blue-600" />
                        ) : (
                          <FolderIcon className="h-6 w-6 text-blue-600" />
                        )}
                      </div>
                    )}
                    <div>
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-600 flex items-center gap-2">
                        {item.name}
                        <ExternalLinkIcon className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </h3>
                      <p className="text-sm text-gray-500">
                        {isSpreadsheet ? (
                          <>
                            <span className="inline-flex items-center">
                              <CalendarIcon className="h-3 w-3 mr-1" />
                              {item.month} {item.year}
                            </span>
                          </>
                        ) : (
                          <span className="capitalize">{item.type.replace(/_/g, ' ')}</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Updated {format(new Date(item.updatedAt), 'MMM d, yyyy')}
                      </p>
                    </div>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      </div>
    </div>
  );
} 