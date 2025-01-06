// src/app/page.tsx
'use client';

import { useSession } from 'next-auth/react';
import { AuthForms } from '@/components/landing/auth-forms';
import { FeaturesGrid } from '@/components/landing/features-grid';
import { GithubBanner } from '@/components/landing/github-banner';
import { HeroSection } from '@/components/landing/hero-section';
import { PoweredBySection } from '@/components/landing/powered-by-section';

export default function Home() {
  const { data: session } = useSession();

  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="w-full max-w-6xl mx-auto px-4 py-12 space-y-20">
        <HeroSection isAuthenticated={!!session} />
        <div className="flex justify-center">
          <AuthForms />
        </div>
        <FeaturesGrid />
        <PoweredBySection />
        <GithubBanner />
      </div>
    </main>
  );
}