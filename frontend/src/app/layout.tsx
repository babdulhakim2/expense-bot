import AuthProvider from "@/app/providers/NextAuthProvider";
import { Toaster } from "@/components/ui/toaster";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { BusinessProvider } from "@/app/providers/BusinessProvider";
import { CSPostHogProvider } from "./providers/CSPostHogProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ExpenseBot - AI-Powered Bookkeeping Assistant",
  description: "Make your expenses less messy.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <CSPostHogProvider>
            <BusinessProvider>
              {children}
              <Toaster />
            </BusinessProvider>
          </CSPostHogProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
