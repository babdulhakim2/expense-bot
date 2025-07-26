'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';

export function BankingCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      // Parse state parameter (should contain encoded businessId and userId)
      if (!state) {
        toast({
          title: "Error",
          description: "Invalid connection state",
          variant: "destructive",
        });
        router.push('/dashboard/settings');
        return;
      }

      let businessId, userId;
      try {
        // Decode the state parameter (should be base64 encoded JSON)
        const stateData = JSON.parse(atob(state));
        businessId = stateData.businessId;
        userId = stateData.userId;
      } catch (error) {
        console.error('Failed to parse state parameter:', error);
        toast({
          title: "Error",
          description: "Invalid connection state format",
          variant: "destructive",
        });
        router.push('/dashboard/settings');
        return;
      }

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
        // Redirect back to settings
        router.push('/dashboard/settings');
      }
    };

    handleCallback();
  }, [router, searchParams, toast]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-2">Connecting your bank...</h1>
        <p className="text-gray-500">Please wait while we complete the connection.</p>
      </div>
    </div>
  );
} 