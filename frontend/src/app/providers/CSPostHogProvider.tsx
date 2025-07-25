"use client";
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';
import { useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface CSPostHogProviderProps {
  children: React.ReactNode;
}

if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    capture_pageview: true,
    capture_pageleave: true,
    
  });
} else if (typeof window !== 'undefined') {
  // Initialize PostHog with minimal config in development
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    capture_pageview: false,
    capture_pageleave: false,

    autocapture: false,
    disable_session_recording: true,
  });
}

export function CSPostHogProvider({ children }: CSPostHogProviderProps) {
  const { data: session } = useSession();

  useEffect(() => {
    // Only identify users in production
    if (process.env.NODE_ENV === 'production' && session?.user) {
      posthog.identify(session.user.id, {
        email: session.user.email,
        name: session.user.name,
      });
    } else if (process.env.NODE_ENV === 'production') {
      // Reset user identification if logged out
      posthog.reset();
    }
  }, [session]);

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}