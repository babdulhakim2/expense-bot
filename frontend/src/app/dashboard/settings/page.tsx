'use client';

import { BusinessSettings } from "@/components/dashboard/settings/business-settings";

export default function SettingsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6 max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        
        <BusinessSettings />
      </div>
    </div>
  );
} 