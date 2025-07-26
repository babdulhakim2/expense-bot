"use client";

import { motion } from 'framer-motion';
import { FolderOpen, ArrowRight, Settings, Check } from 'lucide-react';
import { useState } from 'react';

interface FolderSetupPreviewProps {
  className?: string;
}

export function FolderSetupPreview({ className = "" }: FolderSetupPreviewProps) {
  const [selectedInput, setSelectedInput] = useState('/Messy-Expenses');
  const [selectedOutput, setSelectedOutput] = useState('/Organized-Expenses');
  const [isConfigured, setIsConfigured] = useState(false);

  const handleConfigure = () => {
    setIsConfigured(true);
    setTimeout(() => setIsConfigured(false), 3000);
  };

  return (
    <div className={`bg-card border rounded-xl p-6 ${className}`}>
      <div className="text-center mb-6">
        <div className="inline-flex items-center space-x-2 mb-2">
          <Settings className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Folder Setup Preview</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Configure your two folders for seamless expense organization
        </p>
      </div>

      <div className="space-y-6">
        {/* Input Folder */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-muted-foreground">
            📥 Input Folder (where you upload messy files)
          </label>
          <div className="relative">
            <input
              type="text"
              value={selectedInput}
              onChange={(e) => setSelectedInput(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg bg-orange-50/50 border-orange-200 focus:border-orange-400 focus:outline-none text-sm"
              placeholder="/Drive/Your-Messy-Folder"
            />
            <FolderOpen className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-orange-600" />
          </div>
          <div className="text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded p-2">
            <strong>Example files:</strong> receipt_pic_123.jpg, bank_statement.pdf, random_invoice.png
          </div>
        </div>

        {/* Arrow indicator */}
        <div className="flex justify-center">
          <motion.div
            animate={{ x: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="flex items-center space-x-2 text-muted-foreground"
          >
            <ArrowRight className="w-5 h-5" />
            <span className="text-sm font-medium">AI Processing</span>
            <ArrowRight className="w-5 h-5" />
          </motion.div>
        </div>

        {/* Output Folder */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-muted-foreground">
            📤 Output Folder (where organized files appear)
          </label>
          <div className="relative">
            <input
              type="text"
              value={selectedOutput}
              onChange={(e) => setSelectedOutput(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg bg-green-50/50 border-green-200 focus:border-green-400 focus:outline-none text-sm"
              placeholder="/Drive/Your-Organized-Folder"
            />
            <FolderOpen className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-green-600" />
          </div>
          <div className="text-xs text-green-700 bg-green-50 border border-green-200 rounded p-2">
            <strong>Auto-created structure:</strong> Office Supplies/, Meals & Entertainment/, Transportation/, etc.
          </div>
        </div>

        {/* Preview organized structure */}
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4"
        >
          <div className="text-sm font-medium text-green-800 mb-3">📁 Expected Organization:</div>
          <div className="space-y-1 text-xs text-green-700">
            <div className="flex items-center space-x-2">
              <span>📋</span>
              <span>Office Supplies/</span>
              <span className="text-green-600">• Receipts categorized by vendor</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>🍽️</span>
              <span>Meals & Entertainment/</span>
              <span className="text-green-600">• Restaurant, travel meals</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>🚗</span>
              <span>Transportation/</span>
              <span className="text-green-600">• Uber, gas, parking</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>📊</span>
              <span>Summary Reports/</span>
              <span className="text-green-600">• Monthly expense summaries</span>
            </div>
          </div>
        </motion.div>

        {/* Action button */}
        <motion.button
          onClick={handleConfigure}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            isConfigured
              ? 'bg-green-600 text-white'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {isConfigured ? (
            <div className="flex items-center justify-center space-x-2">
              <Check className="w-4 h-4" />
              <span>Configuration Saved!</span>
            </div>
          ) : (
            'Save Folder Configuration'
          )}
        </motion.button>

        {/* Info note */}
        <div className="text-xs text-muted-foreground text-center bg-muted/30 rounded p-3">
          <strong>Note:</strong> You can change these folders anytime in settings. 
          ExpenseBot will create the output folder structure automatically.
        </div>
      </div>
    </div>
  );
}

export function FolderSetupMini({ className = "" }: { className?: string }) {
  return (
    <div className={`bg-muted/20 border border-border/50 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between space-x-4">
        <div className="flex-1">
          <div className="text-xs font-medium text-muted-foreground mb-1">Input</div>
          <div className="text-sm bg-orange-50 border border-orange-200 rounded px-2 py-1">
            📥 Messy-Expenses/
          </div>
        </div>
        
        <div className="flex flex-col items-center">
          <ArrowRight className="w-4 h-4 text-muted-foreground mb-1" />
          <span className="text-xs text-primary font-medium">AI</span>
        </div>
        
        <div className="flex-1">
          <div className="text-xs font-medium text-muted-foreground mb-1">Output</div>
          <div className="text-sm bg-green-50 border border-green-200 rounded px-2 py-1">
            📤 Organized-Expenses/
          </div>
        </div>
      </div>
    </div>
  );
}