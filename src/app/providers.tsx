// app/providers.js
"use client";
import posthog from 'posthog-js';
import { PostHogProvider } from 'posthog-js/react';
import { useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface CSPostHogProviderProps {
  children: React.ReactNode;
}

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    capture_pageview: true,
    capture_pageleave: true,
    // session_recording: {
    //   enabled: true,
    // },
  });
}

export function CSPostHogProvider({ children }: CSPostHogProviderProps) {
  const { data: session } = useSession();

  useEffect(() => {
    // Identify user when the session changes
    if (session?.user) {
      posthog.identify(session.user.id, {
        email: session.user.email,
        name: session.user.name,
      });
    } else {
      // Reset user identification if logged out
      posthog.reset();
    }
  }, [session]);

  return <PostHogProvider client={posthog}>{children}</PostHogProvider>;
}