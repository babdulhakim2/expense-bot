"use client";

import { Building2Icon, ChevronDown, Plus, Check } from "lucide-react";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { useState, useEffect } from "react";
import {
  BusinessService,
  Business,
} from "@/lib/firebase/services/business-service";
import { useSession } from "next-auth/react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter } from "next/navigation";
import { toast } from "@/hooks/use-toast";
import { NoBusinessFallback } from "./no-business-fallback";

export function BusinessSelector() {
  const { currentBusiness, loadingStates, selectBusiness, refreshBusinesses } =
    useBusiness();
  const { data: session } = useSession();
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loadingBusinesses, setLoadingBusinesses] = useState(false);

  // Load all businesses for the user
  useEffect(() => {
    const loadBusinesses = async () => {
      if (!session?.user?.email) return;

      try {
        setLoadingBusinesses(true);
        const userBusinesses = await BusinessService.getBusinessesByUserEmail(
          session.user.email
        );
        setBusinesses(userBusinesses);
      } catch (error) {
        console.error("Failed to load businesses:", error);
      } finally {
        setLoadingBusinesses(false);
      }
    };

    loadBusinesses();
  }, [session?.user?.email]);

  const handleBusinessSwitch = async (business: Business) => {
    try {
      selectBusiness(business);
      await refreshBusinesses();
      toast({
        title: "Business Switched",
        description: `Now viewing ${business.name}`,
      });
      // Reload the page to refresh all data
      window.location.reload();
    } catch (error) {
      console.error("Failed to switch business:", error);
      toast({
        title: "Error",
        description: "Failed to switch business",
        variant: "destructive",
      });
    }
  };

  const handleCreateNew = () => {
    router.push("/dashboard/settings/business/new");
  };

  if (loadingStates.loading || loadingBusinesses) {
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
    return <NoBusinessFallback />;
  }

  const category =
    BUSINESS_CATEGORIES.find((cat) => cat.id === currentBusiness.type) ||
    BUSINESS_CATEGORIES[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 px-4 py-2 w-full hover:bg-gray-800 rounded-md transition-colors">
          <Building2Icon className="h-5 w-5 flex-shrink-0" />
          <div className="flex-1 min-w-0 text-left">
            <p className="font-medium truncate">{currentBusiness.name}</p>
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <span className="inline-block w-4">{category.icon}</span>
              {category.label}
            </p>
          </div>
          <ChevronDown className="h-4 w-4 text-gray-400" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[240px]">
        <DropdownMenuLabel>Switch Business</DropdownMenuLabel>
        <DropdownMenuSeparator />

        {loadingBusinesses ? (
          <div className="px-2 py-4 text-sm text-muted-foreground text-center">
            Loading businesses...
          </div>
        ) : businesses.length === 0 ? (
          <div className="px-2 py-4 text-sm text-muted-foreground text-center">
            No businesses found
          </div>
        ) : (
          businesses.map((business) => {
            const businessCategory =
              BUSINESS_CATEGORIES.find((cat) => cat.id === business.type) ||
              BUSINESS_CATEGORIES[0];
            const isSelected = business.id === currentBusiness.id;

            return (
              <DropdownMenuItem
                key={business.id}
                onClick={() => !isSelected && handleBusinessSwitch(business)}
                className={isSelected ? "bg-muted" : "cursor-pointer"}
              >
                <Building2Icon className="h-4 w-4 mr-2" />
                <div className="flex-1">
                  <div className="font-medium">{business.name}</div>
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <span>{businessCategory.icon}</span>
                    {businessCategory.label}
                  </div>
                </div>
                {isSelected && <Check className="h-4 w-4 ml-auto" />}
              </DropdownMenuItem>
            );
          })
        )}

        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleCreateNew} className="cursor-pointer">
          <Plus className="h-4 w-4 mr-2" />
          Create New Business
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
