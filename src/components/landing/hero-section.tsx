"use client";

import { motion } from 'framer-motion';
import Image from 'next/image';
import { CheckBusinessView } from '../dashboard/business/check-business-view';
import { TechLogos } from './tech-logos';

interface HeroSectionProps {
  isAuthenticated?: boolean;
}

export function HeroSection({ isAuthenticated }: HeroSectionProps) {
  if (isAuthenticated) {
    return <CheckBusinessView />;
  }

  return (
    <div className="flex flex-col items-center justify-center text-center space-y-12">
      <div className="relative w-[300px] h-[300px] mx-auto">
       

        {/* Tech Logos - Surrounding the Puppy */}
        <TechLogos />
      </div>

      <div className="max-w-2xl mx-auto space-y-4">
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight"
        >
          Smart Bookkeeping,
          <span className="text-primary block mt-1">
            Powered by AI
          </span>
        </motion.h1>

        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="text-base sm:text-lg text-muted-foreground"
        >
          Send receipts via WhatsApp. We'll organize everything in Google Drive.
        </motion.p>
      </div>
    </div>
  );
} 