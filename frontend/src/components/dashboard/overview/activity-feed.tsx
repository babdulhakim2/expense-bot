"use client";

import { useBusiness } from "@/app/providers/BusinessProvider";
import { formatCurrency } from "@/lib/constants/currency";
import { BusinessService } from "@/lib/firebase/services/business-service";
import { formatDistanceToNow } from "date-fns";
import {
  ArrowDownIcon,
  ChevronRightIcon
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

interface AIAction {
  id: string;
  type: string;
  actionData: Record<string, unknown>;
  createdAt: Date;
  relatedId?: string;
  businessId: string;
  message?: string;
  action_type?: string;
  status: "completed" | "processing" | "failed";
  document_type?: string;
  merchant?: string;
  amount?: number;
  // Additional properties used in the component
  month?: string;
  year?: string;
  name?: string;
  content?: string;
  document_url?: string;
  category?: string;
  description?: string;
  timestamp?: string | Date;
}

export function ActivityFeed() {
  const { currentBusiness, hasBusinesses, isInitialized } = useBusiness();
  const [loading, setLoading] = useState(true);
  const [activities, setActivities] = useState<AIAction[]>([]);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    async function loadActivities() {
      try {
        if (currentBusiness) {
          const actions = await BusinessService.getBusinessActions(
            currentBusiness.id
          );
          setActivities(actions as AIAction[]);
        } else {
          // No business - show empty state
          setActivities([]);
        }
      } catch (err) {
        console.error("Error loading activities:", err);
        // On Firebase error, fallback to empty activities instead of showing error
        setActivities([]);
      } finally {
        setLoading(false);
      }
    }

    if (isInitialized) {
      loadActivities();
    }
  }, [currentBusiness, isInitialized]);

  const getActionIcon = (action: AIAction) => {
    switch (action.action_type) {
      case "message_received":
      case "message_sent":
        return "💬";
      case "document_stored":
        return "📄";
      case "spreadsheet_created":
        return "📊";
      case "folder_created":
        return "📁";
      case "transaction_recorded":
        return "💰";
      default:
        return "📋";
    }
  };

  const getActionTitle = (action: AIAction) => {
    switch (action.action_type) {
      case "message_received":
        return "Message received";
      case "message_sent":
        return "Message sent";
      case "document_stored":
        return `${action.document_type
          ?.charAt(0)
          .toUpperCase()}${action.document_type?.slice(1)} stored`;
      case "spreadsheet_created":
        return `Spreadsheet created for ${action.month} ${action.year}`;
      case "folder_created":
        return `Folder "${action.name}" created`;
      case "transaction_recorded":
        return `Transaction recorded${
          action.merchant ? ` for ${action.merchant}` : ""
        }`;
      default:
        return action.action_type?.replace(/_/g, " ") || "Unknown action";
    }
  };

  const getActionDetails = (action: AIAction) => {
    switch (action.action_type) {
      case "message_received":
      case "message_sent":
        if (action.type === "transaction_confirmation") {
          const links = extractLinks(action.content || "");
          const details = parseTransactionMessage(action.content || "");

          return (
            <div className="space-y-1">
              <div className="flex items-center gap-3 text-xs text-gray-600">
                <span>🏷️ {details.category}</span>
                <span>
                  💰{" "}
                  {formatCurrency(
                    parseFloat(details.amount) || 0,
                    currentBusiness?.currency
                  )}
                </span>
                <span>💳 {details.paymentMethod}</span>
                <span>🏢 {details.merchant}</span>
              </div>
              {links.length > 0 && (
                <div className="flex items-center gap-2">
                  {links.map((link, index) => (
                    <Link
                      key={index}
                      href={
                        link.url.includes("drive.google.com")
                          ? `/api/documents/view?url=${encodeURIComponent(
                              link.url
                            )}`
                          : link.url
                      }
                      target="_blank"
                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      🔗 {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        }
        return null;
      case "document_stored":
        return action.document_url ? (
          <Link
            href={`/api/documents/view?url=${encodeURIComponent(
              action.document_url
            )}`}
            target="_blank"
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            🔗 View document
          </Link>
        ) : null;
      case "transaction_recorded":
        return (
          <div className="flex items-center gap-2 text-xs">
            {action.category && (
              <span className="text-gray-600">🏷️ {action.category}</span>
            )}
            {action.amount && (
              <span className="text-gray-600">
                💰 {formatCurrency(action.amount, currentBusiness?.currency)}
              </span>
            )}
            {action.merchant && (
              <span className="text-gray-600">🏢 {action.merchant}</span>
            )}
          </div>
        );
      case "spreadsheet_created":
        return (
          <span className="text-xs text-gray-600">
            📅 {action.month} {action.year}
          </span>
        );
      case "folder_created":
        return <span className="text-xs text-gray-600">💼 {action.name}</span>;
      default:
        return null;
    }
  };

  // Helper functions
  const parseTransactionMessage = (content: string) => {
    const lines = content.split("\n");
    return {
      id:
        lines
          .find((l) => l.includes("🆔"))
          ?.split("🆔")[1]
          .trim() || "",
      amount:
        lines
          .find((l) => l.includes("💰"))
          ?.replace(/💰\s*[\$£€¥]+/, "")
          .trim() || "",
      date:
        lines
          .find((l) => l.includes("📅"))
          ?.split("📅")[1]
          .trim() || "",
      category:
        lines
          .find((l) => l.includes("🏷️"))
          ?.split("🏷️")[1]
          .trim() || "",
      paymentMethod:
        lines
          .find((l) => l.includes("💳"))
          ?.split("💳")[1]
          .trim() || "",
      merchant:
        lines
          .find((l) => l.includes("merchant"))
          ?.split("merchant:")[1]
          .trim() || "",
    };
  };

  const extractLinks = (content: string) => {
    const lines = content.split("\n");
    return lines
      .filter(
        (line) =>
          line.includes("http") && !line.toLowerCase().includes("dashboard")
      )
      .map((line) => {
        const url = line.match(/(https?:\/\/[^\s]+)/g)?.[0] || "";
        const type = line.toLowerCase().includes("spreadsheet")
          ? "spreadsheet"
          : line.toLowerCase().includes("folder")
          ? "folder"
          : "other";
        const label =
          type === "spreadsheet"
            ? "View Spreadsheet"
            : type === "folder"
            ? "Open Folder"
            : "View";
        return { url, type, label };
      });
  };

  if (!isInitialized || loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    );
  }

  // Show empty state if no business
  if (!hasBusinesses || !currentBusiness) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold">Recent AI Activity</h2>
            <p className="text-sm text-gray-500">
              Actions recenly taken by Expense Bot
            </p>
          </div>
        </div>
        <div className="p-8 text-center">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Activity Yet
          </h3>
          <p className="text-gray-500">
            Create a business to start tracking AI activity
          </p>
        </div>
      </div>
    );
  }

  const displayedActivities = showAll ? activities : activities.slice(0, 5);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Recent AI Activity</h2>
            <p className="text-sm text-gray-500">
              Actions recenly taken by Expense Bot
            </p>
          </div>
          {activities.length > 5 && (
            <Link
              href="/dashboard/activity"
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              View all <ChevronRightIcon className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="p-8 text-center">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Activity Yet
          </h3>
          <p className="text-gray-500">
            Start uploading documents to see AI activity here
          </p>
        </div>
      ) : (
        <>
          <div className="divide-y divide-gray-100">
            {displayedActivities.map((activity) => (
              <div
                key={activity.id}
                className={`px-3 py-2 hover:bg-gray-50 transition-colors border-l-2 ${
                  activity.status === "completed"
                    ? "border-l-green-500"
                    : activity.status === "processing"
                    ? "border-l-blue-500"
                    : "border-l-red-500"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{getActionIcon(activity)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-900">
                        {getActionTitle(activity)}
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-400">
                        {formatDistanceToNow(
                          new Date(activity.timestamp || activity.createdAt),
                          { addSuffix: true }
                        )}
                      </span>
                      {activity.status === "completed" && (
                        <span className="text-green-600">✓</span>
                      )}
                      {activity.status === "processing" && (
                        <span className="text-blue-600 animate-pulse">⏳</span>
                      )}
                      {activity.status === "failed" && (
                        <span className="text-red-600">❌</span>
                      )}
                    </div>
                    <div className="mt-1 text-xs">
                      {getActionDetails(activity)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {activities.length > 5 && !showAll && (
            <div className="p-4 border-t border-gray-100">
              <button
                onClick={() => setShowAll(true)}
                className="w-full text-sm text-gray-600 hover:text-gray-900 flex items-center justify-center gap-2"
              >
                Show more <ArrowDownIcon className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
