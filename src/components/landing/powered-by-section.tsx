"use client";

import { motion } from 'framer-motion';
import { Brain, Cpu } from 'lucide-react';

export function PoweredBySection() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8, duration: 0.5 }}
      className="mt-20 pt-10 border-t"
    >
      <div className="flex flex-col items-center space-y-6">
        <motion.div 
          className="flex items-center space-x-2 text-muted-foreground"
          whileHover={{ scale: 1.02 }}
        >
          <Brain className="w-5 h-5 text-primary" />
          <span>Powered by</span>
        </motion.div>
        
        <div className="flex flex-wrap justify-center gap-4 items-center">
          <motion.a
            href="https://blog.google/technology/developers/gemma-open-models/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-4 py-2 rounded-full bg-card hover:bg-primary/10 border border-primary/20 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
          >
            <Cpu className="w-4 h-4 text-primary" />
            <span className="font-semibold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Gemma 2
            </span>
          </motion.a>

          <motion.a
            href="https://www.kaggle.com/models/google/paligemma"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-4 py-2 rounded-full bg-card hover:bg-secondary/30 border border-secondary/20 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
          >
            <Brain className="w-4 h-4 text-secondary-foreground" />
            <span className="font-semibold bg-gradient-to-r from-secondary-foreground to-secondary-foreground/70 bg-clip-text text-transparent">
              PalliGemma
            </span>
          </motion.a>
        </div>
        
        <p className="text-sm text-muted-foreground max-w-md text-center">
          Leveraging Google's advanced AI models for intelligent receipt processing and analysis
        </p>
      </div>
    </motion.div>
  );
} 