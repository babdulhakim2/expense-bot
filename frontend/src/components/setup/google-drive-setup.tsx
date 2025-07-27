"use client";

import { motion } from 'framer-motion';
import { FolderOpen, ArrowRight, Settings, Check, ExternalLink, AlertCircle, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';
import { BusinessService, type GoogleDriveConfig } from '@/lib/firebase/services/business-service';

interface GoogleDriveSetupProps {
  businessId: string;
  onComplete?: (config: GoogleDriveConfig) => void;
  onSkip?: () => void;
  className?: string;
}

export function GoogleDriveSetup({ businessId, onComplete, onSkip, className = "" }: GoogleDriveSetupProps) {
  const [inputFolder, setInputFolder] = useState('/Messy-Expenses');
  const [outputFolder, setOutputFolder] = useState('/Organized-Expenses');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // Check if Google Drive was just connected
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('google_drive') === 'connected') {
      setIsConnected(true);
    }
  }, []);

  const handleConnectGoogleDrive = async () => {
    try {
      setIsConnecting(true);
      setConnectionError(null);

      const response = await fetch(`/api/auth/google-drive?businessId=${businessId}&redirectUrl=/setup`);
      
      if (!response.ok) {
        throw new Error('Failed to get authorization URL');
      }

      const { authUrl } = await response.json();
      
      // Redirect to Google OAuth
      window.location.href = authUrl;
    } catch (error) {
      console.error('Error connecting to Google Drive:', error);
      setConnectionError('Failed to connect to Google Drive. Please try again.');
      setIsConnecting(false);
    }
  };

  const handleSaveConfiguration = async () => {
    try {
      if (!isConnected) {
        await handleConnectGoogleDrive();
        return;
      }

      // Create folders in Google Drive
      const response = await fetch('/api/google-drive/create-folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          businessId,
          inputFolderPath: inputFolder,
          outputFolderPath: outputFolder,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create folders');
      }

      const { inputFolder: createdInputFolder, outputFolder: createdOutputFolder } = await response.json();

      toast({
        title: "Configuration Saved!",
        description: `Created folders: ${createdInputFolder.name} and ${createdOutputFolder.name}`,
      });

      onComplete?.({
        inputFolderPath: inputFolder,
        outputFolderPath: outputFolder,
        inputFolderId: createdInputFolder.id,
        outputFolderId: createdOutputFolder.id,
        connectedAt: new Date(),
      });
    } catch (error) {
      console.error('Error saving configuration:', error);
      toast({
        title: "Error",
        description: "Failed to create folders. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleSkip = () => {
    onSkip?.();
  };

  return (
    <div className={`bg-card border rounded-xl p-6 ${className}`}>
      <div className="text-center mb-6">
        <div className="inline-flex items-center space-x-2 mb-2">
          <Settings className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold">Connect Your Google Drive</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Optional: Connect your Google Drive for personalized folder organization
        </p>
      </div>

      {!isConnected ? (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="text-2xl">🔗</div>
              <div className="flex-1">
                <h4 className="font-medium text-blue-900 mb-1">Why connect Google Drive?</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Create folders directly in your personal Google Drive</li>
                  <li>• Generate expense spreadsheets in your account</li>
                  <li>• Keep all your data under your control</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="text-sm font-medium text-gray-700">
              We'll request permission to:
            </div>
            <div className="bg-gray-50 border rounded-lg p-3">
              <div className="space-y-2 text-xs text-gray-600">
                <div className="flex items-center space-x-2">
                  <Check className="w-3 h-3 text-green-600" />
                  <span>Create and organize folders in your Google Drive</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Check className="w-3 h-3 text-green-600" />
                  <span>Create and edit spreadsheets for expense reports</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Check className="w-3 h-3 text-green-600" />
                  <span>Read folder metadata to organize your expenses</span>
                </div>
              </div>
            </div>
          </div>

          {connectionError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm text-red-800">{connectionError}</span>
              </div>
            </div>
          )}

          <div className="flex space-x-3">
            <Button 
              onClick={handleConnectGoogleDrive}
              disabled={isConnecting}
              className="flex-1"
            >
              {isConnecting ? (
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Connecting...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <ExternalLink className="w-4 h-4" />
                  <span>Connect Google Drive</span>
                </div>
              )}
            </Button>
            <Button variant="outline" onClick={handleSkip}>
              Skip for now
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Input Folder */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-muted-foreground">
              📥 Input Folder (where you upload messy files)
            </label>
            <div className="relative">
              <input
                type="text"
                value={inputFolder}
                onChange={(e) => setInputFolder(e.target.value)}
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
                value={outputFolder}
                onChange={(e) => setOutputFolder(e.target.value)}
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

          <Button onClick={handleSaveConfiguration} className="w-full">
            <div className="flex items-center space-x-2">
              <Check className="w-4 h-4" />
              <span>Save Folder Configuration</span>
            </div>
          </Button>
        </div>
      )}

      {/* Info note */}
      <div className="text-xs text-muted-foreground text-center bg-muted/30 rounded p-3 mt-4">
        <strong>Note:</strong> You can change these settings anytime in your business settings. 
        {!isConnected && " Skipping will use our shared folders instead."}
      </div>
    </div>
  );
}