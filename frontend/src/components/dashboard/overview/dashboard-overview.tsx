'use client';

import { BusinessService } from '@/lib/firebase/services/business-service';
import { subMonths } from 'date-fns';
import {
  ArrowDownIcon,
  ArrowUpIcon,
  BarChart3Icon,
  FileSpreadsheetIcon,
  MessageSquareIcon,
  ReceiptIcon,
  UploadCloudIcon
} from "lucide-react";
import { useSession } from 'next-auth/react';
import { useCallback, useEffect, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { ActivityFeed } from './activity-feed';
import { toast } from "@/hooks/use-toast"

interface Action {
  id: string;
  action_type: string;
  status: string;
  timestamp: string;
  amount?: number;
}

interface Stats {
  label: string;
  value: string | number;
  icon: any;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  tooltip?: string;
}

export function DashboardOverview() {
  const { data: session } = useSession();
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Stats[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        if (session?.user?.email) {
          const business = await BusinessService.getBusinessByUserEmail(session.user.email);
          if (business) {
            const actions = await BusinessService.getBusinessActions(business.id);
            setActions(actions as any);
            calculateStats(actions as any) ;
          }
        }
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [session]);

  const calculateStats = (actions: Action[]) => {
    const now = new Date();
    const lastMonth = subMonths(now, 1);

    // Current month's actions
    const currentMonthActions = actions.filter(
      a => new Date(a.timestamp) >= lastMonth
    );

    // Previous month's actions for comparison
    const previousMonthActions = actions.filter(
      a => new Date(a.timestamp) >= subMonths(lastMonth, 1) && 
          new Date(a.timestamp) < lastMonth
    );

    const calculateChange = (current: number, previous: number) => {
      if (previous === 0) return current > 0 ? '+100%' : '0%';
      const change = ((current - previous) / previous) * 100;
      return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
    };

    const getTrend = (current: number, previous: number): 'up' | 'down' | 'neutral' => {
      if (current === previous) return 'neutral';
      return current > previous ? 'up' : 'down';
    };

    // Calculate specific metrics
    const currentMessages = currentMonthActions.filter(
      a => a.action_type === 'message_received' || a.action_type === 'message_sent'
    ).length;
    const previousMessages = previousMonthActions.filter(
      a => a.action_type === 'message_received' || a.action_type === 'message_sent'
    ).length;

    const currentReceipts = currentMonthActions.filter(
      a => a.action_type === 'document_stored'
    ).length;
    const previousReceipts = previousMonthActions.filter(
      a => a.action_type === 'document_stored'
    ).length;

    const currentTransactions = currentMonthActions.filter(
      a => a.action_type === 'transaction_recorded'
    );
    const previousTransactions = previousMonthActions.filter(
      a => a.action_type === 'transaction_recorded'
    );

    const currentAmount = currentTransactions.reduce((sum, t) => sum + (t.amount || 0), 0);
    const previousAmount = previousTransactions.reduce((sum, t) => sum + (t.amount || 0), 0);

    const newStats: Stats[] = [
      {
        label: 'Messages Processed',
        value: currentMessages,
        icon: MessageSquareIcon,
        change: calculateChange(currentMessages, previousMessages),
        trend: getTrend(currentMessages, previousMessages),
        tooltip: 'Total WhatsApp messages processed this month'
      },
      {
        label: 'Receipts Processed',
        value: currentReceipts,
        icon: ReceiptIcon,
        change: calculateChange(currentReceipts, previousReceipts),
        trend: getTrend(currentReceipts, previousReceipts),
        tooltip: 'Documents and receipts processed this month'
      },
      {
        label: 'Transactions',
        value: currentTransactions.length,
        icon: BarChart3Icon,
        change: calculateChange(currentTransactions.length, previousTransactions.length),
        trend: getTrend(currentTransactions.length, previousTransactions.length),
        tooltip: 'Total transactions recorded this month'
      },
      {
        label: 'Total Amount',
        value: `£${currentAmount.toFixed(2)}`,
        icon: FileSpreadsheetIcon,
        change: calculateChange(currentAmount, previousAmount),
        trend: getTrend(currentAmount, previousAmount),
        tooltip: 'Total transaction amount this month'
      }
    ];

    setStats(newStats);
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Warn if multiple files are dropped
    if (acceptedFiles.length > 1) {
      toast({
        title: "Only one file allowed",
        description: "Please upload files one at a time",
      });
    }

    // Take only the first file
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    try {
      // Get the business ID first
      const business = await BusinessService.getBusinessByUserEmail(session?.user?.email!);
      if (!business) {
        throw new Error('No active business found');
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('businessId', business.id);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to upload file');
      }

      // Show success toast
      toast({
        title: "Success",
        description: `Successfully processed ${file.name}`,
      })

      // Refresh actions and stats
      const newActions = await BusinessService.getBusinessActions(business.id);
      setActions(newActions as any);
      calculateStats(newActions as any);

    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message || 'Failed to process file',
      })
    } finally {
      setUploading(false);
    }
  }, [session?.user?.email]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    multiple: false,
    maxFiles: 1,
    onDropRejected: (rejectedFiles) => {
      if (rejectedFiles.length > 1) {
        toast({
          title: "Multiple files detected",
          description: "Please upload only one file at a time",
          variant: "destructive"
        });
      } else {
        // Handle other rejection reasons (file type, size, etc.)
        const error = rejectedFiles[0]?.errors[0];
        if (error) {
          toast({
            title: "Invalid file",
            description: error.message,
            variant: "destructive"
          });
        }
      }
    }
  });

  return (
    <div className="p-6 space-y-6">
      {/* Bulk Upload dropzone */}
      <div 
        {...getRootProps()} 
        className={`
          w-full border-2 border-dashed rounded-xl p-8
          transition-colors duration-200 ease-in-out cursor-pointer
          min-h-[180px] flex items-center justify-center
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 bg-white'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} disabled={uploading} />
        <div className="flex flex-col items-center justify-center gap-3">
          <UploadCloudIcon className={`h-12 w-12 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
          <p className="text-sm text-gray-600 text-center">
            {uploading ? (
              "Processing file..."
            ) : isDragActive ? (
              "Drop your file here..."
            ) : (
              <>
                Drag & drop a file here, or <span className="text-blue-500">click to select file</span>
                <br />
                <span className="text-xs text-gray-500">
                  Supports PDF and images (PNG, JPG)
                </span>
              </>
            )}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
            title={stat.tooltip}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <h3 className="text-2xl font-semibold mt-1">{stat.value}</h3>
              </div>
              <div className="h-12 w-12 bg-blue-50 rounded-full flex items-center justify-center">
                <stat.icon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center">
              {stat.trend === 'up' ? (
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
              ) : stat.trend === 'down' ? (
                <ArrowDownIcon className="h-4 w-4 text-red-500" />
              ) : (
                <div className="h-4 w-4" /> // Placeholder for neutral trend
              )}
              <span className={`ml-1 text-sm ${
                stat.trend === 'up' ? 'text-green-500' : 
                stat.trend === 'down' ? 'text-red-500' : 
                'text-gray-500'
              }`}>
                {stat.change}
              </span>
              <span className="ml-2 text-sm text-gray-500">vs last month</span>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Feed */}
      <ActivityFeed />
    </div>
  );
} 