import { FileSpreadsheetIcon, FolderIcon, MoreVerticalIcon, PlusIcon, SearchIcon, StarIcon } from "lucide-react";

type Folder = {
  id: string;
  name: string;
  type: 'folder' | 'spreadsheet';
  updatedAt: string;
  itemCount?: number;
  starred?: boolean;
  lastModifiedBy?: string;
};

const mockFolders: Folder[] = [
  {
    id: '1',
    name: 'Tax Documents 2024',
    type: 'folder',
    updatedAt: '2024-03-15',
    itemCount: 8,
    starred: true,
    lastModifiedBy: 'AI Assistant'
  },
  {
    id: '2',
    name: 'Monthly Expenses',
    type: 'folder',
    updatedAt: '2024-03-14',
    itemCount: 12,
    lastModifiedBy: 'AI Assistant'
  },
  {
    id: '3',
    name: 'Q1 Financial Report',
    type: 'spreadsheet',
    updatedAt: '2024-03-13',
    lastModifiedBy: 'You'
  },
  {
    id: '4',
    name: 'Investment Tracking',
    type: 'spreadsheet',
    updatedAt: '2024-03-12',
    starred: true,
    lastModifiedBy: 'AI Assistant'
  },
];

export default function FoldersPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Folders</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your financial documents and spreadsheets</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            <PlusIcon className="h-4 w-4" />
            New Folder
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search folders and files..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select className="px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>All Items</option>
            <option>Folders Only</option>
            <option>Spreadsheets Only</option>
            <option>Starred</option>
          </select>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {mockFolders.map((item) => (
            <div
              key={item.id}
              className="group relative bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {item.type === 'folder' ? (
                    <div className="p-2 bg-blue-50 rounded-lg">
                      <FolderIcon className="h-6 w-6 text-blue-600" />
                    </div>
                  ) : (
                    <div className="p-2 bg-green-50 rounded-lg">
                      <FileSpreadsheetIcon className="h-6 w-6 text-green-600" />
                    </div>
                  )}
                  <div>
                    <h3 className="font-medium text-gray-900 group-hover:text-blue-600">
                      {item.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {item.type === 'folder' ? `${item.itemCount} items` : 'Spreadsheet'} • Updated {item.updatedAt}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Last modified by {item.lastModifiedBy}
                    </p>
                  </div>
                </div>
                <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded-full transition-opacity">
                  <MoreVerticalIcon className="h-4 w-4 text-gray-500" />
                </button>
              </div>
              {item.starred && (
                <div className="absolute top-2 right-2">
                  <StarIcon className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 