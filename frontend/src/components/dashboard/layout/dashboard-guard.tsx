"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useBusiness } from "@/app/providers/BusinessProvider";
import { Loader2, Building } from "lucide-react";

interface DashboardGuardProps {
  children: React.ReactNode;
}

export function DashboardGuard({ children }: DashboardGuardProps) {
  const router = useRouter();
  const { currentBusiness, hasBusinesses, isInitialized, loadingStates } =
    useBusiness();

  useEffect(() => {
    if (!isInitialized) return;

    if (!hasBusinesses || !currentBusiness) {
      router.push("/setup");
      return;
    }
  }, [isInitialized, hasBusinesses, currentBusiness, router]);

  if (!isInitialized || loadingStates.loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">
              Loading Dashboard...
            </h2>
            <p className="text-gray-600">Preparing your business workspace</p>
          </div>
        </div>
      </div>
    );
  }

  if (!hasBusinesses || !currentBusiness) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Building className="h-12 w-12 text-primary mx-auto" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">
              Setting up workspace...
            </h2>
            <p className="text-gray-600">Redirecting you to business setup</p>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
