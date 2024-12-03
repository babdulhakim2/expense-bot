import { authOptions } from "@/lib/auth";
import { getServerSession } from "next-auth/next";
import { redirect } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard/layout/dashboard-layout";

export default async function DashboardRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/");
  }

  return <DashboardLayout>{children}</DashboardLayout>;
} 