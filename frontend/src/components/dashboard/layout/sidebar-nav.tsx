'use client';

import { WhatsAppQR } from '@/components/shared/whatsapp-qr';
import { cn } from "@/lib/utils";
import {
  FolderIcon,
  HomeIcon,
  QrCodeIcon
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { SmartBusinessSelector } from '../business/smart-business-selector';

const navigationItems = [
  { name: 'Overview', href: '/dashboard', icon: HomeIcon },
  { name: 'Drive', href: '/dashboard/folders', icon: FolderIcon },
];

export function SidebarNav() {
  const pathname = usePathname();
  const [showQR, setShowQR] = useState(false);

  return (
    <div className="flex h-full w-[240px] flex-col bg-gray-900 text-white">
      <div className="p-6 border-b border-gray-800">
        <Link href='/' >
          <h2 className="text-xl font-bold mb-4">Expense Bot</h2>
        </Link>
        <SmartBusinessSelector />
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navigationItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center px-3 py-2 text-sm rounded-md gap-x-3 transition-colors",
              pathname === item.href
                ? "bg-gray-800 text-white" 
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </Link>
        ))}
      </nav>

      {/* WhatsApp QR Code Button */}
      <div className="px-3 py-2">
        <button
          onClick={() => setShowQR(true)}
          className="flex items-center w-full px-3 py-2 text-sm text-gray-300 rounded-md hover:bg-gray-800 hover:text-white"
        >
          <QrCodeIcon className="h-5 w-5 mr-3" />
          Show WhatsApp QR
        </button>
      </div>


      {/* QR Code Modal */}
      {showQR && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <div className="text-center space-y-4">
              <h2 className="text-2xl font-bold text-gray-900">Connect with ExpenseBot</h2>
              <p className="text-gray-600">
                Scan the QR code with your phone&apos;s camera or click below to open WhatsApp
              </p>
              <div className="flex justify-center">
                <WhatsAppQR size={240} />
              </div>
              <button 
                onClick={() => setShowQR(false)}
                className="mt-4 px-4 py-2 border border-gray-200 rounded-md hover:bg-gray-100 text-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 