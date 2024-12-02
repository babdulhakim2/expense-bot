'use client';

import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-6 max-w-md">
        {/* Simple Error Icon */}
        <div className="mx-auto w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
          <span className="text-4xl text-red-600 font-bold">!</span>
        </div>

        {/* Text Content */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">Something Went Wrong</h1>
          <p className="text-gray-600">
            We apologize for the inconvenience. An unexpected error occurred while processing your request.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <button
            onClick={reset}
            className="inline-flex w-full sm:w-auto justify-center px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex w-full sm:w-auto justify-center px-8 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>

        {/* Error Details */}
        <div className="mt-8 text-left bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm font-medium text-gray-700">Error Details:</p>
          <p className="text-sm text-gray-500 mt-1 font-mono break-all">
            {error.message || "An unknown error occurred"}
          </p>
          {error.digest && (
            <p className="text-xs text-gray-400 mt-2">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        {/* Help Text */}
        <p className="text-sm text-gray-500 pt-6">
          If this problem persists, please contact our support team for assistance.
        </p>
      </div>

      {/* Decorative Elements */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-orange-500"></div>
      <div className="absolute bottom-8 left-0 right-0 flex justify-center text-gray-400 text-sm">
        Error 500
      </div>
    </div>
  );
} 