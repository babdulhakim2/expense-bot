"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { useSession } from "next-auth/react";

export function HeroSection() {
  const { data: session } = useSession();

  return (
    <div className="flex flex-col items-center justify-center text-center gap-8 pt-16 pb-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight"
        >
          Let AI Organize Your
          <span className="text-primary block mt-1">
            Expenses in Google Drive
          </span>
        </motion.h1>

        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="text-base sm:text-lg text-muted-foreground max-w-2xl"
        >
          Transform your messy financial documents into organized Google Sheets and folders.
          Ask questions about your expenses and get instant AI-powered answers.
          Harness the power of Google Sheets for effortless financial management.
        </motion.p>

        {/* Call to Action */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="flex justify-center"
        >
          {session ? (
            <Link href="/dashboard">
              <Button size="lg" className="gap-2 text-base px-8 py-3 h-auto">
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          ) : (
            <Link href="/auth/login">
              <Button size="lg" className="gap-2 text-base px-8 py-3 h-auto">
                Get Started for Free
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          )}
        </motion.div>

        {/* Hero Illustration Placeholder */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="w-full max-w-4xl mx-auto mt-8 mb-4"
        >
          <div className="bg-gradient-to-r from-muted/30 to-muted/50 rounded-xl p-4 sm:p-8 border border-border/50 backdrop-blur-sm">
            <div className="flex flex-col sm:flex-row items-center justify-center space-y-6 sm:space-y-0 sm:space-x-8">
              {/* Before - Messy Folder */}
              <div className="flex-1 text-center w-full">
                <div className="bg-red-50 dark:bg-red-950/30 border-2 border-red-200 dark:border-red-800 rounded-lg p-4 sm:p-6 mb-3">
                  <div className="text-red-600 dark:text-red-400 text-sm font-medium mb-2">
                    📁 Messy Expenses
                  </div>
                  <div className="space-y-1 text-xs text-red-700 dark:text-red-300">
                    <div>receipt_pic_123.jpg</div>
                    <div>bank_statement_old.pdf</div>
                    <div>random_receipt.png</div>
                    <div>invoice_scan.jpeg</div>
                  </div>
                </div>
                <span className="text-sm text-muted-foreground">
                  Your chaotic uploads
                </span>
              </div>

              {/* Arrow */}
              <div className="flex sm:flex-col items-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-2">
                  <span className="text-2xl">🤖</span>
                </div>
                <div className="text-sm font-medium text-primary">AI Magic</div>
              </div>

              {/* After - Organized Google Sheets */}
              <div className="flex-1 text-center w-full">
                <div className="bg-green-50 dark:bg-green-950/30 border-2 border-green-200 dark:border-green-800 rounded-lg p-4 sm:p-6 mb-3">
                  <div className="text-green-600 dark:text-green-400 text-sm font-medium mb-2">
                    📊 Smart Google Sheets
                  </div>
                  <div className="space-y-1 text-xs text-green-700 dark:text-green-300">
                    <div>🍽️ Restaurant: $45.20</div>
                    <div>🚗 Uber: $23.50</div>
                    <div>📋 Office: $112.80</div>
                    <div>💬 "Total spent on meals?"</div>
                  </div>
                </div>
                <span className="text-sm text-muted-foreground">
                  Searchable & trackable
                </span>
              </div>
            </div>

            {/* Mobile-friendly call to action */}
            <div className="mt-6 pt-6 border-t border-border/50 text-center">
              <p className="text-xs text-muted-foreground">
                Ask questions, get answers, and track expenses with the power of Google Sheets and AI
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
