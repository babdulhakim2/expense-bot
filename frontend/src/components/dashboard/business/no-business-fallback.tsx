"use client";

import { Building2Icon, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { useState } from "react";
import { BusinessQuickCreateForm } from "./business-quick-create-form";
import { toast } from "@/hooks/use-toast";

interface NoBusinessFallbackProps {
  showInDashboard?: boolean;
  message?: string;
  description?: string;
}

export function NoBusinessFallback({
  showInDashboard = false,
  message = "No Business Selected",
  description = "Create your first business to get started with ExpenseBot",
}: NoBusinessFallbackProps) {
  const { loadingStates } = useBusiness();
  const [showQuickCreate, setShowQuickCreate] = useState(false);

  if (showInDashboard) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="max-w-md mx-auto text-center space-y-6 p-8">
          {showQuickCreate ? (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <BusinessQuickCreateForm
                onSuccess={(business) => {
                  setShowQuickCreate(false);
                  toast({
                    title: "Business Created",
                    description: `${business.name} is now active`,
                  });
                }}
                onCancel={() => setShowQuickCreate(false)}
                isCreating={loadingStates.creating}
              />
            </div>
          ) : (
            <>
              {/* Icon */}
              <div className="flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mx-auto">
                <Building2Icon className="h-10 w-10 text-gray-400" />
              </div>

              {/* Message */}
              <div className="space-y-2">
                <h2 className="text-xl font-semibold text-gray-900">
                  {message}
                </h2>
                <p className="text-gray-600 max-w-sm mx-auto">{description}</p>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <Button
                  onClick={() => setShowQuickCreate(true)}
                  className="w-full max-w-xs"
                  disabled={loadingStates.creating}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Business
                </Button>

                <p className="text-xs text-gray-500">
                  You can also create a business from the sidebar
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // Compact version for smaller spaces
  return (
    <div className="text-center space-y-4 p-4">
      <div className="flex items-center justify-center w-16 h-16 bg-gray-100 rounded-lg mx-auto">
        <Building2Icon className="h-8 w-8 text-gray-400" />
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-medium text-gray-900">{message}</h3>
        <p className="text-sm text-gray-600 max-w-xs mx-auto">{description}</p>
      </div>

      {showQuickCreate ? (
        <BusinessQuickCreateForm
          onSuccess={(business) => {
            setShowQuickCreate(false);
            toast({
              title: "Business Created",
              description: `${business.name} is now active`,
            });
          }}
          onCancel={() => setShowQuickCreate(false)}
          isCreating={loadingStates.creating}
        />
      ) : (
        <Button
          onClick={() => setShowQuickCreate(true)}
          size="sm"
          disabled={loadingStates.creating}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Business
        </Button>
      )}
    </div>
  );
}
