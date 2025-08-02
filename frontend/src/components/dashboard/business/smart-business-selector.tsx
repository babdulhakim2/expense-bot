"use client";

import { Building2Icon, ChevronDown, Plus, Check, Loader2 } from "lucide-react";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { BUSINESS_CATEGORIES } from "@/lib/constants/business-categories";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { BusinessCreateDialog } from "./business-create-dialog";

export function SmartBusinessSelector() {
  const {
    businesses,
    currentBusiness,
    loadingStates,
    hasBusinesses,
    isInitialized,
    selectBusiness,
  } = useBusiness();

  const [showCreateDialog, setShowCreateDialog] = useState(false);

  if (!isInitialized || loadingStates.loading) {
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

  // No businesses state - show creation prompt
  if (!hasBusinesses) {
    return (
      <>
        <div className="px-4 py-2">
          <div className="text-center space-y-3">
            <div className="flex items-center justify-center w-12 h-12 bg-gray-800 rounded-lg mx-auto">
              <Building2Icon className="h-6 w-6 text-gray-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">
                No business selected
              </p>
              <p className="text-xs text-gray-500">
                Create your first business to get started
              </p>
            </div>
            <Button
              onClick={() => setShowCreateDialog(true)}
              size="sm"
              className="w-full"
              disabled={loadingStates.creating}
            >
              {loadingStates.creating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Business
                </>
              )}
            </Button>
          </div>
        </div>
        <BusinessCreateDialog
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
          onSuccess={(business) => {
            toast({
              title: "Business Created",
              description: `${business.name} is now active`,
            });
          }}
        />
      </>
    );
  }

  const category = currentBusiness
    ? BUSINESS_CATEGORIES.find((cat) => cat.id === currentBusiness.type) ||
      BUSINESS_CATEGORIES[0]
    : BUSINESS_CATEGORIES[0];

  const handleBusinessSwitch = async (business: (typeof businesses)[0]) => {
    try {
      selectBusiness(business);
      toast({
        title: "Business Switched",
        description: `Now viewing ${business.name}`,
      });
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
    setShowCreateDialog(true);
  };

  return (
    <>
      <div className="px-4 py-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 w-full hover:bg-gray-800 rounded-md transition-colors p-2"
              disabled={loadingStates.switching}
            >
              <Building2Icon className="h-5 w-5 flex-shrink-0" />
              <div className="flex-1 min-w-0 text-left">
                {currentBusiness ? (
                  <>
                    <p className="font-medium truncate">
                      {currentBusiness.name}
                    </p>
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                      <span className="inline-block w-4">{category.icon}</span>
                      {category.label}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="font-medium text-gray-300">Select Business</p>
                    <p className="text-xs text-gray-500">
                      Choose from {businesses.length} businesses
                    </p>
                  </>
                )}
              </div>
              {loadingStates.switching ? (
                <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-[240px]">
            <DropdownMenuLabel>Switch Business</DropdownMenuLabel>
            <DropdownMenuSeparator />

            {businesses.map((business) => {
              const businessCategory =
                BUSINESS_CATEGORIES.find((cat) => cat.id === business.type) ||
                BUSINESS_CATEGORIES[0];
              const isSelected = business.id === currentBusiness?.id;

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
            })}

            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleCreateNew}
              className="cursor-pointer"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create New Business
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      
      <BusinessCreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={(business) => {
          toast({
            title: "Business Created",
            description: `${business.name} is now active`,
          });
        }}
      />
    </>
  );
}
