'use client';

import {
    FileSpreadsheetIcon,
    FolderIcon
} from "lucide-react";

export function BusinessSettings() {
  return (
    <div className="space-y-6">
      {/* Business Profile */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Business Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Business Name</label>
              <input 
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter business name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Business Type</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                <option>Retail</option>
                <option>Technology</option>
                <option>Services</option>
                <option>Manufacturing</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Registration Number</label>
              <input 
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter registration number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Tax ID</label>
              <input 
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter tax ID"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Financial Settings */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Financial Settings</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Default Currency</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                <option>GBP (£)</option>
                <option>USD ($)</option>
                <option>EUR (€)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Financial Year End</label>
              <input 
                type="date"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          {/* Categories */}
          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">Expense Categories</label>
            <div className="border border-gray-200 rounded-md p-4 space-y-2">
              {/* Add category tags with remove buttons */}
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-sm">
                  Office Supplies
                  <button className="ml-2 text-gray-500 hover:text-gray-700">×</button>
                </span>
                <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 text-sm">
                  Travel
                  <button className="ml-2 text-gray-500 hover:text-gray-700">×</button>
                </span>
                <button className="inline-flex items-center px-3 py-1 rounded-full border border-dashed border-gray-300 text-sm text-gray-500 hover:text-gray-700">
                  + Add Category
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Settings */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Integrations</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-md">
              <div className="flex items-center gap-3">
                <FileSpreadsheetIcon className="h-6 w-6 text-green-600" />
                <div>
                  <h3 className="font-medium">Google Sheets</h3>
                  <p className="text-sm text-gray-500">Connected</p>
                </div>
              </div>
              <button className="text-sm text-blue-600 hover:text-blue-700">Configure</button>
            </div>
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-md">
              <div className="flex items-center gap-3">
                <FolderIcon className="h-6 w-6 text-blue-600" />
                <div>
                  <h3 className="font-medium">Google Drive</h3>
                  <p className="text-sm text-gray-500">Connected</p>
                </div>
              </div>
              <button className="text-sm text-blue-600 hover:text-blue-700">Configure</button>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Save Changes
        </button>
      </div>
    </div>
  );
} 