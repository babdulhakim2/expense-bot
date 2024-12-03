'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BusinessSettings } from "@/components/dashboard/settings/business-settings";
import { ProfileSettings } from "@/components/dashboard/settings/profile-settings";
import { NotificationSettings } from "@/components/dashboard/settings/notification-settings";

export default function SettingsPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6 max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        
        <Tabs defaultValue="business" className="space-y-6">
          <TabsList>
            <TabsTrigger value="business">Business</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
          </TabsList>

          <TabsContent value="business">
            <BusinessSettings />
          </TabsContent>

          <TabsContent value="profile">
            <ProfileSettings />
          </TabsContent>

          <TabsContent value="notifications">
            <NotificationSettings />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 