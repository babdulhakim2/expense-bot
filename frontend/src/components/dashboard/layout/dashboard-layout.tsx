'use client';

import { SidebarNav } from "./sidebar-nav";
import { DashboardHeader } from "./header";
import { BusinessProvider } from "@/app/providers/BusinessProvider";
import { Business } from "@/lib/firebase/services/business-service";

interface DashboardLayoutProps {
  children: React.ReactNode;
  initialBusinesses?: Business[];
}

export function DashboardLayout({ children, initialBusinesses }: DashboardLayoutProps) {
  return (
    <BusinessProvider initialBusinesses={initialBusinesses}>
      <div className="flex h-screen bg-gray-50">
        <SidebarNav />
        <div className="flex-1 flex flex-col overflow-hidden">
          <DashboardHeader />
          {children}
        </div>
      </div>
    </BusinessProvider>
  );
} 