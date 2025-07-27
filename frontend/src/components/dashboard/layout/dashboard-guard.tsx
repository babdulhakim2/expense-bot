"use client";

import { Business } from "@/lib/firebase/services/business-service";

interface DashboardGuardProps {
  children: React.ReactNode;
  initialBusinesses?: Business[];
}

export function DashboardGuard({
  children,
  initialBusinesses,
}: DashboardGuardProps) {
  if (initialBusinesses && initialBusinesses.length > 0) {
    return <>{children}</>;
  }

  return <>{children}</>;
}
