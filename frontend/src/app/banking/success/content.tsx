'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, Loader2 } from "lucide-react";

export function BankingSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [syncStatus, setSyncStatus] = useState('syncing');

  useEffect(() => {
    const connectionId = searchParams.get('connection_id');
    if (!connectionId) {
      router.push('/dashboard/settings');
      return;
    }

    // Start initial sync
    const syncTransactions = async () => {
      try {
        const response = await fetch('/api/banking/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            connection_id: connectionId,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to sync transactions');
        }

        setSyncStatus('completed');
        
        // Redirect after 2 seconds
        setTimeout(() => {
          router.push('/dashboard/settings');
        }, 2000);

      } catch (error) {
        console.error('Sync error:', error);
        setSyncStatus('error');
      }
    };

    syncTransactions();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center p-6 bg-white rounded-lg shadow-lg max-w-md">
        <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">
          Bank Connected Successfully!
        </h1>
        <div className="mb-6">
          {syncStatus === 'syncing' ? (
            <div className="flex items-center justify-center gap-2 text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Syncing your transactions...</span>
            </div>
          ) : syncStatus === 'completed' ? (
            <p className="text-green-600">All transactions synced!</p>
          ) : (
            <p className="text-red-600">Failed to sync transactions</p>
          )}
        </div>
        <p className="text-gray-500 text-sm">
          You will be redirected to your dashboard shortly...
        </p>
      </div>
    </div>
  );
} 