'use client';

import { cn } from "@/lib/utils";
import { 
  HomeIcon, 
  FolderIcon, 
  FileSpreadsheetIcon, 
  ClockIcon,
  SettingsIcon,
  LogOutIcon 
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import { LogOut, MessageCircle } from "lucide-react";
import { BusinessSwitcher } from '../business/business-switcher';

const navigationItems = [
  { name: 'Overview', href: '/dashboard', icon: HomeIcon },
  { name: 'Folders', href: '/dashboard/folders', icon: FolderIcon },
  { name: 'Spreadsheets', href: '/dashboard/spreadsheets', icon: FileSpreadsheetIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: SettingsIcon },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-[240px] flex-col bg-gray-900 text-white">
      <div className="p-6 border-b border-gray-800">
        <h2 className="text-xl font-bold mb-4">Financial Hub</h2>
        <BusinessSwitcher />
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm rounded-md gap-x-3 transition-colors",
                isActive 
                  ? "bg-gray-800 text-white" 
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={() => signOut()}
          className="flex items-center px-3 py-2 text-sm text-gray-300 rounded-md hover:bg-gray-800 hover:text-white w-full"
        >
          <LogOutIcon className="h-5 w-5 mr-3" />
          Sign out
        </button>
      </div>
    </div>
  );
} 