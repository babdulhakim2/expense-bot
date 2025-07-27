'use client';

import { SidebarNav } from "./sidebar-nav";
import { DashboardHeader } from "./header";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-50">
      <SidebarNav />
      <div className="flex-1 flex flex-col overflow-hidden">
        <DashboardHeader />
        {children}
      </div>
    </div>
  );
} 