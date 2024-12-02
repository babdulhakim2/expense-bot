"use client";

import { motion } from 'framer-motion';
import Image from 'next/image';

export function HeroSection() {
  return (
    <div className="flex flex-col items-center text-center space-y-8">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ 
          type: "spring",
          stiffness: 260,
          damping: 20,
          duration: 0.6 
        }}
        whileHover={{ 
          scale: 1.05,
          rotate: [-1, 1, -1, 0],
          transition: { duration: 0.4 } 
        }}
        className="relative"
      >
        <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-full blur opacity-75 group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-pulse"/>
        <Image 
          src="/logo.png" 
          alt="ExpenseBot Logo - Friendly AI Assistant Puppy" 
          width={200} 
          height={200}
          className="relative rounded-full shadow-lg"
          priority
        />
      </motion.div>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
          Your AI-Powered
          <motion.span
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="text-primary block"
          >
            Bookkeeping Assistant
          </motion.span>
        </h1>
      </motion.div>

      <motion.p
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="text-xl text-muted-foreground max-w-2xl"
      >
        Simplify your bookkeeping with ExpenseBot. Just send your receipts via WhatsApp, 
        and let AI handle the rest.
      </motion.p>
    </div>
  );
} 