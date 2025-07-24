'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function BankingErrorPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center p-6 bg-white rounded-lg shadow-lg max-w-md">
        <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Connection Failed
        </h1>
        <p className="text-gray-600 mb-6">
          We encountered an error while connecting your bank account. Please try again.
        </p>
        <div className="space-y-3">
          <Button
            onClick={() => router.push('/dashboard/settings')}
            className="w-full bg-purple-600 hover:bg-purple-700"
          >
            Return to Settings
          </Button>
          <Button
            variant="outline"
            onClick={() => router.back()}
            className="w-full"
          >
            Try Again
          </Button>
        </div>
      </div>
    </div>
  );
} 