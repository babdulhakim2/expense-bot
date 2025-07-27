import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";
import { getServerSession } from "next-auth/next";
import { redirect } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard/layout/dashboard-layout";
import { DashboardGuard } from "@/components/dashboard/layout/dashboard-guard";
import { getServerBusinesses } from "./actions";

export default async function DashboardRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions) as any; // eslint-disable-line @typescript-eslint/no-explicit-any

  if (!session) {
    redirect("/");
  }

  // Server-side business loading using Firebase service
  const businesses = await getServerBusinesses();

  // Redirect to setup if no businesses found
  if (!businesses || businesses.length === 0) {
    redirect("/setup");
  }

  return (
    <DashboardGuard initialBusinesses={businesses}>
      <DashboardLayout initialBusinesses={businesses}>{children}</DashboardLayout>
    </DashboardGuard>
  );
} 