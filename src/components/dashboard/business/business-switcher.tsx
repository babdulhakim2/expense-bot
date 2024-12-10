'use client';

import { Building2Icon, ChevronDownIcon, PlusCircleIcon, Settings2Icon } from "lucide-react";
import { useState } from "react";
import { useBusiness } from "@/contexts/business-context";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { useRouter } from "next/navigation";
import { toast } from "@/hooks/use-toast";
import { useSession } from "next-auth/react";

export function BusinessSwitcher() {
  const router = useRouter();
  const { data: session } = useSession();
  const { businesses, currentBusiness, setCurrentBusiness, isLoading } = useBusiness();
  const [isOpen, setIsOpen] = useState(false);

  if (isLoading || !session?.user) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 animate-pulse">
        <div className="h-5 w-5 bg-gray-700 rounded" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-700 rounded w-24" />
          <div className="h-3 bg-gray-700 rounded w-16" />
        </div>
      </div>
    );
  }

  const handleBusinessSwitch = async (business: typeof currentBusiness) => {
    if (!business || !session?.user?.id) return;
    
    try {
      setCurrentBusiness(business);
      setIsOpen(false);
      
      toast({
        title: "Business Switched",
        description: `Switched to ${business.name}`,
      });
    } catch (error) {
      console.error('Error switching business:', error);
      toast({
        title: "Error",
        description: "Failed to switch business",
        variant: "destructive",
      });
    }
  };

  const getBusinessCategory = (type: string) => {
    return BUSINESS_CATEGORIES.find(cat => cat.id === type) || BUSINESS_CATEGORIES[0];
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 w-full text-left text-sm hover:bg-gray-800 rounded-md"
      >
        <Building2Icon className="h-5 w-5" />
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{currentBusiness?.name || 'Select Business'}</p>
          {currentBusiness && (
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <span className="inline-block w-4">{getBusinessCategory(currentBusiness.type).icon}</span>
              {getBusinessCategory(currentBusiness.type).label}
            </p>
          )}
        </div>
        <ChevronDownIcon className="h-4 w-4 opacity-50" />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 w-full mt-2 py-2 bg-gray-900 rounded-md shadow-lg border border-gray-800 z-50">
          {businesses.length > 0 ? (
            <div className="px-2 pb-2 mb-2 border-b border-gray-800">
              <p className="px-2 pb-1.5 text-xs font-medium text-gray-400">
                Your Businesses
              </p>
              {businesses.map((business) => (
                <button
                  key={business.id}
                  onClick={() => handleBusinessSwitch(business)}
                  className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded"
                >
                  <span className="inline-block w-4 text-center">
                    {getBusinessCategory(business.type).icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{business.name}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {getBusinessCategory(business.type).label}
                    </p>
                  </div>
                  {business.id === currentBusiness?.id && (
                    <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-2 text-sm text-gray-400">
              No businesses yet
            </div>
          )}
          
          <div className="px-2">
            <button
              onClick={() => {
                router.push('/dashboard/settings/business/new');
                setIsOpen(false);
              }}
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded text-blue-400"
            >
              <PlusCircleIcon className="h-4 w-4" />
              Add Business
            </button>
            {currentBusiness && (
              <button
                onClick={() => {
                  router.push('/dashboard/settings/business');
                  setIsOpen(false);
                }}
                className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-800 rounded"
              >
                <Settings2Icon className="h-4 w-4" />
                Business Settings
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 