import AuthProvider from "@/components/providers/next-auth-provider";
import { Toaster } from "@/components/ui/toaster";
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { BusinessProvider } from '@/contexts/business-context';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ExpenseBot - AI-Powered Bookkeeping Assistant',
  description: 'Simplify your bookkeeping with ExpenseBot. Send receipts via WhatsApp and let AI handle the rest.',
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
          <BusinessProvider>
            {children}
            <Toaster />
          </BusinessProvider>
        </AuthProvider>
      </body>
    </html>
  );
}