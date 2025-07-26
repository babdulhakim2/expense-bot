"use client";

import { Building2Icon } from "lucide-react";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";

export function BusinessInfo() {
  const { currentBusiness, loadingStates } = useBusiness();

  if (loadingStates.loading) {
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
  if (!currentBusiness) {
    return (
      <div className="px-4 py-2 text-sm text-gray-400">No business access</div>
    );
  }

  const category =
    BUSINESS_CATEGORIES.find((cat) => cat.id === currentBusiness.type) ||
    BUSINESS_CATEGORIES[0];

  return (
    <div className="flex items-center gap-2 px-4 py-2">
      <Building2Icon className="h-5 w-5" />
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{currentBusiness.name}</p>
        <p className="text-xs text-gray-400 flex items-center gap-1">
          <span className="inline-block w-4">{category.icon}</span>
          {category.label}
        </p>
      </div>
    </div>
  );
}
