import { FileSpreadsheetIcon, PlusIcon, SearchIcon, StarIcon, BarChart2Icon } from "lucide-react";

type Spreadsheet = {
  id: string;
  name: string;
  category: string;
  updatedAt: string;
  rowCount: number;
  starred?: boolean;
  lastModifiedBy?: string;
  hasCharts?: boolean;
};

const mockSpreadsheets: Spreadsheet[] = [
  {
    id: '1',
    name: 'Monthly Budget 2024',
    category: 'Budgeting',
    updatedAt: '2024-03-15',
    rowCount: 156,
    starred: true,
    lastModifiedBy: 'AI Assistant',
    hasCharts: true
  },
  {
    id: '2',
    name: 'Q1 Expense Tracking',
    category: 'Expenses',
    updatedAt: '2024-03-14',
    rowCount: 89,
    lastModifiedBy: 'AI Assistant',
    hasCharts: true
  },
  {
    id: '3',
    name: 'Annual Tax Summary',
    category: 'Taxes',
    updatedAt: '2024-03-13',
    rowCount: 245,
    lastModifiedBy: 'You'
  },
  {
    id: '4',
    name: 'Investment Portfolio',
    category: 'Investments',
    updatedAt: '2024-03-12',
    rowCount: 67,
    starred: true,
    lastModifiedBy: 'AI Assistant',
    hasCharts: true
  },
];

export default function SpreadsheetsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Spreadsheets</h1>
            <p className="text-sm text-gray-500 mt-1">View and manage your financial spreadsheets</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            <PlusIcon className="h-4 w-4" />
            New Spreadsheet
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search spreadsheets..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select className="px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option>All Categories</option>
            <option>Budgeting</option>
            <option>Expenses</option>
            <option>Taxes</option>
            <option>Investments</option>
          </select>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {mockSpreadsheets.map((sheet) => (
            <div
              key={sheet.id}
              className="group relative bg-white p-4 rounded-lg border border-gray-200 hover:border-green-400 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-50 rounded-lg">
                    <FileSpreadsheetIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 group-hover:text-green-600">
                      {sheet.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-gray-500">
                        {sheet.rowCount} rows
                      </span>
                      {sheet.hasCharts && (
                        <span className="flex items-center text-xs text-gray-400">
                          <BarChart2Icon className="h-3 w-3 mr-1" />
                          Charts
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Last modified by {sheet.lastModifiedBy}
                    </p>
                  </div>
                </div>
              </div>
              {sheet.starred && (
                <div className="absolute top-2 right-2">
                  <StarIcon className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                </div>
              )}
              <div className="absolute bottom-2 right-2">
                <span className="inline-flex items-center px-2 py-1 rounded-full bg-gray-100 text-xs font-medium text-gray-600">
                  {sheet.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 