// src/app/page.tsx
'use client';

import { useSession } from 'next-auth/react';
import { FeaturesGrid } from '@/components/landing/features-grid';
import { HowItWorks } from '@/components/landing/how-it-works';
import { GithubBanner } from '@/components/landing/github-banner';
import { HeroSection } from '@/components/landing/hero-section';
import { PoweredBySection } from '@/components/landing/powered-by-section';
import { AccountMenu } from '@/components/landing/account-menu';
import { useEffect } from 'react';
import posthog from 'posthog-js';

export default function Home() {
  const { data: session } = useSession();

  useEffect(() => {
    // Identify user when they're logged in
    if (session?.user) {
      posthog.identify(session.user.id, {
        email: session.user.email,
        name: session.user.name,
      });
    }
  }, [session]);

  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">ExpenseBot</h2>
            {session && (
              <div className="hidden sm:flex items-center text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded-full">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Signed in
              </div>
            )}
          </div>
          {session ? <AccountMenu /> : null}
        </div>
      </header>
      
      <div className="w-full max-w-6xl mx-auto px-4">
        {/* Hero Section */}
        <HeroSection />

        {/* Marketing sections */}
        <div className="space-y-20 py-20">
          <HowItWorks />
          <FeaturesGrid />
          <PoweredBySection />
          <GithubBanner />
        </div>
      </div>
    </main>
  );
}