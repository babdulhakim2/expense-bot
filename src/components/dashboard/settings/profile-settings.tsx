'use client';

import { UserIcon, PhoneIcon, AtSignIcon, ShieldIcon } from "lucide-react";

export function ProfileSettings() {
  return (
    <div className="space-y-6">
      {/* Personal Information */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Full Name</label>
              <input 
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email Address</label>
              <input 
                type="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone Number</label>
              <input 
                type="tel"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your WhatsApp number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                <option>Business Owner</option>
                <option>Accountant</option>
                <option>Manager</option>
                <option>Employee</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Security</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Current Password</label>
              <input 
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter current password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">New Password</label>
              <input 
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter new password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Confirm New Password</label>
              <input 
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Confirm new password"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Two-Factor Authentication */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Two-Factor Authentication</h2>
              <p className="text-sm text-gray-500 mt-1">Add an extra layer of security to your account</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
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