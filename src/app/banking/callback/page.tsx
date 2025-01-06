
import { Suspense } from 'react';
import { BankingCallbackContent } from './content';

export default function BankingCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-2">Connecting your bank...</h1>
          <p className="text-gray-500">Please wait while we complete the connection.</p>
        </div>
      </div>
    }>
      <BankingCallbackContent />
    </Suspense>
  );
} 