// 'use client';

import Link from "next/link";
import { FileQuestionIcon, HomeIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-6 max-w-md">
        {/* Icon */}
        <div className="relative mx-auto w-24 h-24">
          <div className="absolute inset-0 bg-blue-100 rounded-full animate-pulse"></div>
          <div className="relative flex items-center justify-center w-full h-full">
            <FileQuestionIcon className="w-12 h-12 text-blue-600" />
          </div>
        </div>

        {/* Text Content */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">Page Not Found</h1>
          <p className="text-gray-600">
            Oops! It seems the financial document you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link href="/dashboard" className="w-full sm:w-auto">
            <Button size="lg" className="w-full gap-2">
              <HomeIcon className="w-4 h-4" />
              Back to Dashboard
            </Button>
          </Link>
         
        </div>

        {/* Help Text */}
        <p className="text-sm text-gray-500 pt-6">
          If you believe this is an error, please contact support or try refreshing the page.
        </p>
      </div>

      {/* Decorative Elements */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      <div className="absolute bottom-8 left-0 right-0 flex justify-center text-gray-400 text-sm">
        Error 404
      </div>
    </div>
  );
} 