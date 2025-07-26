import { useState } from 'react';

export type BankConnection = {
  id: string;
  bankName: string;
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
  accountCount: number;
  createdAt: string;
  updatedAt: string;
};

export function useBankConnection() {
  const [isConnecting, setIsConnecting] = useState(false);

  const connectBank = async (userId: string, businessId: string) => {
    try {
      setIsConnecting(true);

      // 1. Get link token
      const linkTokenResponse = await fetch('/api/banking/plaid', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          action: 'create_link_token',
          user_id: userId,
        }),
      });

      // Check if response is JSON
      const contentType = linkTokenResponse.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await linkTokenResponse.text();
        console.error('Non-JSON response:', text);
        throw new Error('Invalid response from server');
      }

      const data = await linkTokenResponse.json();
      
      if (!linkTokenResponse.ok) {
        throw new Error(data.error || 'Failed to get link token');
      }

      const { link_token } = data;
      if (!link_token) {
        throw new Error('No link token received from server');
      }

      // 2. Initialize Plaid Link
      const { open } = await loadPlaidLink(link_token);
      
      // 3. Open Plaid Link and wait for success
      return new Promise((resolve, reject) => {
        const handler = (event: MessageEvent) => {
          if (event.data.type === 'PLAID_LINK_SUCCESS') {
            const { public_token } = event.data;
            
            // 4. Exchange public token
            fetch('/api/banking/plaid', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                action: 'exchange_token',
                public_token,
                user_id: userId,
                business_id: businessId,
              }),
            })
            .then(response => response.json())
            .then(result => {
              if (!result.connection_id) {
                throw new Error('Failed to exchange token');
              }
              window.removeEventListener('message', handler);
              resolve(result);
            })
            .catch(error => {
              window.removeEventListener('message', handler);
              reject(error);
            });
          } else if (event.data.type === 'PLAID_LINK_ERROR') {
            window.removeEventListener('message', handler);
            reject(new Error('Plaid Link failed'));
          } else if (event.data.type === 'PLAID_LINK_EXIT') {
            window.removeEventListener('message', handler);
            reject(new Error('Link cancelled'));
          }
        };

        window.addEventListener('message', handler);
        open();
      });

    } catch (error) {
      console.error('Bank connection error:', error);
      throw error;
    } finally {
      setIsConnecting(false);
    }
  };

  return {
    connectBank,
    isConnecting,
  };
}

// Helper function to load Plaid Link
function loadPlaidLink(linkToken: string) {
  return new Promise<{ open: () => void }>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js';
    script.onload = () => {
      // @ts-expect-error Plaid SDK is loaded dynamically and types are not available
      const handler = Plaid.create({
        token: linkToken,
        onSuccess: (public_token: string) => {
          window.postMessage({ 
            type: 'PLAID_LINK_SUCCESS',
            public_token 
          }, window.location.origin);
        },
        onExit: () => {
          window.postMessage({ 
            type: 'PLAID_LINK_EXIT' 
          }, window.location.origin);
        },
        onError: (err: Error) => {
          window.postMessage({ 
            type: 'PLAID_LINK_ERROR',
            error: err 
          }, window.location.origin);
        },
      });
      resolve({ open: () => handler.open() });
    };
    script.onerror = reject;
    document.body.appendChild(script);
  });
} 