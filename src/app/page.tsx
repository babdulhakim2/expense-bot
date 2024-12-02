// src/app/page.tsx
'use client';

import { AuthForms } from '@/components/landing/auth-forms';
import { FeaturesGrid } from '@/components/landing/features-grid';
import { GithubBanner } from '@/components/landing/github-banner';
import { HeroSection } from '@/components/landing/hero-section';
import { PoweredBySection } from '@/components/landing/powered-by-section';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary">
      <div className="container mx-auto px-4 pt-20 pb-16">
        <HeroSection />
        <AuthForms />
        <FeaturesGrid />
        <PoweredBySection />
        <GithubBanner />
      </div>
    </main>
  );
}