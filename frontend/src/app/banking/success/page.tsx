
import { Suspense } from 'react';
import { BankingSuccessContent } from './content';

export default function BankingSuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center p-6 bg-white rounded-lg shadow-lg max-w-md">
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">
            Loading...
          </h1>
        </div>
      </div>
    }>
      <BankingSuccessContent />
    </Suspense>
  );
} 