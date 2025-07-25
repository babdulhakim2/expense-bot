"use client";

import { motion } from 'framer-motion';
import { Cloud, FolderOpen, Sparkles, ArrowRight } from 'lucide-react';
import { useInView } from 'react-intersection-observer';
import { FolderSetupPreview } from './folder-setup-preview';

const steps = [
  {
    icon: <Cloud className="w-12 h-12 text-blue-600 mb-4" />,
    title: "Connect Google Drive",
    description: "Link your Google Drive account to get started. Don't worry - you can skip this step and set it up later.",
    highlight: "Optional onboarding",
    visual: (
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 w-full max-w-xs mx-auto">
        <div className="flex items-center space-x-2 mb-3">
          <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
            <Cloud className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-medium text-blue-800">Google Drive</span>
        </div>
        <div className="text-xs text-blue-700 space-y-1">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Connected</span>
          </div>
          <div className="text-blue-600">Ready to organize!</div>
        </div>
      </div>
    )
  },
  {
    icon: <FolderOpen className="w-12 h-12 text-amber-600 mb-4" />,
    title: "Set Your Folders",
    description: "Choose two folders: one where you'll dump all your messy receipts and documents, and another where AI will organize everything perfectly.",
    highlight: "2-folder setup",
    visual: (
      <div className="space-y-3 w-full max-w-xs mx-auto">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div className="text-orange-700 text-sm font-medium mb-1">📥 Input Folder</div>
          <div className="text-xs text-orange-600">/Drive/Messy-Expenses</div>
        </div>
        <div className="flex justify-center">
          <ArrowRight className="w-4 h-4 text-muted-foreground" />
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="text-green-700 text-sm font-medium mb-1">📤 Output Folder</div>
          <div className="text-xs text-green-600">/Drive/Organized-Expenses</div>
        </div>
      </div>
    )
  },
  {
    icon: <Sparkles className="w-12 h-12 text-purple-600 mb-4" />,
    title: "Upload & Let AI Work",
    description: "Drop your receipts, invoices, and financial documents into your input folder. AI automatically categorizes, extracts data, and organizes everything.",
    highlight: "Automatic processing",
    visual: (
      <div className="w-full max-w-xs mx-auto">
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4">
          <div className="text-center mb-3">
            <div className="inline-flex items-center space-x-1 text-purple-700 text-sm font-medium">
              <Sparkles className="w-4 h-4" />
              <span>AI Processing</span>
            </div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-purple-700">Text extracted</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-purple-700">Category assigned</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-purple-700">File organized</span>
            </div>
          </div>
        </div>
      </div>
    )
  }
];

export function HowItWorks() {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1
  });

  return (
    <motion.div 
      ref={ref}
      className="py-20"
    >
      <div className="text-center mb-16">
        <motion.h2
          initial={{ y: 20, opacity: 0 }}
          animate={inView ? { y: 0, opacity: 1 } : {}}
          transition={{ duration: 0.5 }}
          className="text-3xl sm:text-4xl font-bold mb-4"
        >
          How It Works
        </motion.h2>
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={inView ? { y: 0, opacity: 1 } : {}}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-lg text-muted-foreground max-w-2xl mx-auto"
        >
          Three simple steps to transform your financial chaos into organized clarity
        </motion.p>
      </div>

      <div className="grid lg:grid-cols-3 gap-12 lg:gap-8">
        {steps.map((step, index) => (
          <motion.div
            key={index}
            initial={{ y: 50, opacity: 0 }}
            animate={inView ? { y: 0, opacity: 1 } : {}}
            transition={{ delay: index * 0.2 + 0.4, duration: 0.6 }}
            className="relative"
          >
            {/* Step number */}
            <div className="absolute -top-4 -left-4 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold text-sm z-10">
              {index + 1}
            </div>
            
            {/* Card */}
            <div className="bg-card border rounded-xl p-8 h-full hover:shadow-lg transition-shadow duration-300">
              <div className="text-center">
                {step.icon}
                
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                
                <div className="inline-block bg-primary/10 text-primary text-xs font-medium px-3 py-1 rounded-full mb-4">
                  {step.highlight}
                </div>
                
                <p className="text-muted-foreground mb-6 leading-relaxed">
                  {step.description}
                </p>
                
                {/* Visual preview */}
                <div className="mt-auto">
                  {step.visual}
                </div>
              </div>
            </div>
            
            {/* Connector line for desktop */}
            {index < steps.length - 1 && (
              <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-border -translate-y-1/2">
                <div className="absolute right-0 top-1/2 w-2 h-2 bg-primary rounded-full -translate-y-1/2 translate-x-1"></div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Interactive Folder Setup Preview */}
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={inView ? { y: 0, opacity: 1 } : {}}
        transition={{ delay: 1.0, duration: 0.5 }}
        className="mt-16"
      >
        <div className="text-center mb-8">
          <h3 className="text-2xl font-semibold mb-3">Try the Folder Setup</h3>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            See how easy it is to configure your expense organization system. 
            Customize the folder paths to match your Google Drive structure.
          </p>
        </div>
        <div className="max-w-2xl mx-auto">
          <FolderSetupPreview />
        </div>
      </motion.div>

      {/* Call to action */}
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={inView ? { y: 0, opacity: 1 } : {}}
        transition={{ delay: 1.4, duration: 0.5 }}
        className="text-center mt-16"
      >
        <div className="bg-muted/30 rounded-xl p-8 border border-border/50">
          <h3 className="text-xl font-semibold mb-3">Ready to Get Organized?</h3>
          <p className="text-muted-foreground mb-6">
            Join thousands of users who've transformed their expense management with AI
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Free to start</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Google Drive integration</span>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>AI-powered organization</span>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}