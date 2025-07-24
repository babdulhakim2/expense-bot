// src/app/page.tsx
'use client';

import { useSession } from 'next-auth/react';
import { AuthForms } from '@/components/landing/auth-forms';
import { FeaturesGrid } from '@/components/landing/features-grid';
import { GithubBanner } from '@/components/landing/github-banner';
import { HeroSection } from '@/components/landing/hero-section';
import { PoweredBySection } from '@/components/landing/powered-by-section';
// import { useEffect } from 'react';
// import posthog from 'posthog-js';

export default function Home() {
  const { data: session } = useSession();

  // useEffect(() => {
  //   // Identify user when they're logged in
  //   if (session?.user) {
  //     posthog.identify(session.user.id, {
  //       email: session.user.email,
  //       name: session.user.name,
  //     });
  //   }
  // }, [session]);

  return (
    <main className="min-h-screen flex flex-col">
      <div className="w-full max-w-6xl mx-auto px-4">
        {/* Hero and Auth section */}
        <div className="flex flex-col">
          <HeroSection isAuthenticated={!!session} />
          <div className="flex justify-center -mt-2 sm:-mt-4">
            <AuthForms />
          </div>
        </div>

        {/* Rest of the sections */}
        <div className="space-y-20 py-20">
          <FeaturesGrid />
          <PoweredBySection />
          <GithubBanner />
        </div>
      </div>
    </main>
  );
}