'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';

export default function BankingCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      // Get stored connection state
      const storedState = localStorage.getItem('bankConnectionState');
      if (!storedState) {
        toast({
          title: "Error",
          description: "Invalid connection state",
          variant: "destructive",
        });
        router.push('/dashboard/settings');
        return;
      }

      const { businessId, userId } = JSON.parse(storedState);

      try {
        const response = await fetch('/api/banking/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            state,
            business_id: businessId,
            user_id: userId,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to complete bank connection');
        }

        toast({
          title: "Success",
          description: "Bank connected successfully",
        });

      } catch (error) {
        console.error('Callback error:', error);
        toast({
          title: "Error",
          description: "Failed to complete bank connection",
          variant: "destructive",
        });
      } finally {
        // Clean up
        localStorage.removeItem('bankConnectionState');
        // Redirect back to settings
        router.push('/dashboard/settings');
      }
    };

    handleCallback();
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-2">Connecting your bank...</h1>
        <p className="text-gray-500">Please wait while we complete the connection.</p>
      </div>
    </div>
  );
} 