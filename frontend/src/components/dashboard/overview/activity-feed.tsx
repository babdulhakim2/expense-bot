"use client";

import { BusinessService } from "@/lib/firebase/services/business-service";

interface AIAction {
  id: string;
  type: string;
  actionData: Record<string, unknown>;
  createdAt: Date;
  relatedId?: string;
  businessId: string;
}
import { formatDistanceToNow } from "date-fns";
import {
  AlertCircleIcon,
  ArrowDownIcon,
  BarChartIcon,
  BuildingIcon,
  CalendarIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  CreditCardIcon,
  DollarSignIcon,
  ExternalLinkIcon,
  FileIcon,
  FileSpreadsheetIcon,
  FolderIcon,
  FolderTreeIcon,
  HashIcon,
  LinkIcon,
  LoaderIcon,
  MessageSquareIcon,
  ReceiptIcon,
  TableIcon,
  TagIcon,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useBusiness } from "@/app/providers/BusinessProvider";


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
          setActivities(actions);
        } else {
          // No business - show empty state
          setActivities([]);
        }
      } catch (err) {
        console.error("Error loading activities:", err);
        // On Firebase error, fallback to empty activities instead of showing error
        setActivities([]);
        setError(null); // Don't show error to user
      } finally {
        setLoading(false);
      }
    }

    if (isInitialized) {
      loadActivities();
    }
  }, [currentBusiness, isInitialized]);

  const getActionIcon = (action: Action) => {
    const baseClass = "h-5 w-5";
    const statusColors: { [key: string]: string } = {
      completed: "text-green-600",
      processing: "text-blue-600",
      failed: "text-red-600",
    };
    const color = statusColors[action.status] || "text-gray-600";

    switch (action.action_type) {
      case "message_received":
      case "message_sent":
        return <MessageSquareIcon className={`${baseClass} ${color}`} />;
      case "document_stored":
        return <ReceiptIcon className={`${baseClass} ${color}`} />;
      case "spreadsheet_created":
        return <FileSpreadsheetIcon className={`${baseClass} ${color}`} />;
      case "folder_created":
        return <FolderIcon className={`${baseClass} ${color}`} />;
      case "transaction_recorded":
        return action.amount ? (
          <div className={`${color} font-semibold`}>
            £{action.amount.toFixed(2)}
          </div>
        ) : (
          <FileIcon className={`${baseClass} ${color}`} />
        );
      default:
        return <FileIcon className={`${baseClass} ${color}`} />;
    }
  };

  const getActionTitle = (action: Action) => {
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
        return action.action_type.replace(/_/g, " ");
    }
  };

  const getActionDetails = (action: Action) => {
    switch (action.action_type) {
      case "message_received":
      case "message_sent":
        if (action.type === "transaction_confirmation") {
          const links = extractLinks(action.content || "");
          const details = parseTransactionMessage(action.content || "");

          return (
            <div className="space-y-3">
              {/* Transaction Details Section */}
              <div className="grid grid-cols-2 gap-2 bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center gap-2 text-sm">
                  <HashIcon className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-600 font-mono">{details.id}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <DollarSignIcon className="h-4 w-4 text-emerald-500" />
                  <span className="font-semibold">£{details.amount}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CalendarIcon className="h-4 w-4 text-blue-400" />
                  <span>{details.date}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CreditCardIcon className="h-4 w-4 text-purple-400" />
                  <span>{details.paymentMethod}</span>
                </div>
                <div className="col-span-2 flex items-center gap-2 text-sm">
                  <BuildingIcon className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">{details.merchant}</span>
                </div>
                <div className="col-span-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <TagIcon className="h-3 w-3 mr-1" />
                    {details.category}
                  </span>
                </div>
              </div>

              {/* Quick Links Section */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quick Access
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {links.map((link, index) => (
                    <Link
                      key={index}
                      href={link.url}
                      target="_blank"
                      className={`flex items-center gap-2 p-2 rounded-md text-sm transition-colors ${getLinkStyle(
                        link.type
                      )}`}
                    >
                      {getLinkIcon(link.type)}
                      <span className="truncate">{link.label}</span>
                      <ExternalLinkIcon className="h-3 w-3 flex-shrink-0 ml-auto" />
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          );
        }
        return action.content || "No content";
      case "document_stored":
        return action.document_url ? (
          <Link
            href={action.document_url}
            target="_blank"
            className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            View document <ExternalLinkIcon className="h-3 w-3" />
          </Link>
        ) : null;
      case "transaction_recorded":
        return (
          <div className="flex flex-wrap gap-2">
            {action.category && (
              <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-50 text-xs font-medium text-blue-700">
                {action.category}
              </span>
            )}
            {action.description && (
              <span className="text-gray-600">{action.description}</span>
            )}
          </div>
        );
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
          ?.split("£")[1]
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

  const getLinkStyle = (type: string) => {
    switch (type) {
      case "spreadsheet":
        return "bg-emerald-50 text-emerald-700 hover:bg-emerald-100";
      case "folder":
        return "bg-blue-50 text-blue-700 hover:bg-blue-100";
      case "dashboard":
        return "bg-purple-50 text-purple-700 hover:bg-purple-100";
      default:
        return "bg-gray-50 text-gray-700 hover:bg-gray-100";
    }
  };

  const getLinkIcon = (type: string) => {
    switch (type) {
      case "spreadsheet":
        return <TableIcon className="h-4 w-4" />;
      case "folder":
        return <FolderTreeIcon className="h-4 w-4" />;
      case "dashboard":
        return <BarChartIcon className="h-4 w-4" />;
      default:
        return <LinkIcon className="h-4 w-4" />;
    }
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
              Real-time updates of AI processing
            </p>
          </div>
        </div>
        <div className="p-8 text-center">
          <MessageSquareIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
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
              Real-time updates of AI processing
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
          <MessageSquareIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
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
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`p-2 rounded-lg ${
                      activity.status === "completed"
                        ? "bg-green-50"
                        : activity.status === "processing"
                        ? "bg-blue-50"
                        : "bg-red-50"
                    }`}
                  >
                    {getActionIcon(activity)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {getActionTitle(activity)}
                      </span>
                      {activity.status === "completed" && (
                        <CheckCircleIcon className="h-4 w-4 text-green-600" />
                      )}
                      {activity.status === "processing" && (
                        <LoaderIcon className="h-4 w-4 text-blue-600 animate-spin" />
                      )}
                      {activity.status === "failed" && (
                        <AlertCircleIcon className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                    <div className="mt-1">{getActionDetails(activity)}</div>
                    <p className="text-xs text-gray-400 mt-2">
                      {formatDistanceToNow(new Date(activity.timestamp), {
                        addSuffix: true,
                      })}
                    </p>
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
