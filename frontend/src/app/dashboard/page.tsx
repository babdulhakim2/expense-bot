import { DashboardHeader } from "@/components/dashboard/layout/header";
import { DashboardOverview } from "@/components/dashboard/overview/dashboard-overview";

export default function DashboardPage() {
  return (
    <>
      <DashboardHeader />
      <main className="flex-1 overflow-y-auto">
        <DashboardOverview />
      </main>
    </>
  );
}
