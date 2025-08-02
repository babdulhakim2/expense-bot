"use client";

import { useBusiness } from "@/app/providers/BusinessProvider";
import { formatCurrency } from "@/lib/constants/currency";
import {
  BuildingIcon,
  CalendarIcon,
  DollarSignIcon,
  ExternalLinkIcon,
  TagIcon,
} from "lucide-react";

export interface SearchResult {
  id: string;
  document_id: string;
  content: string;
  score: number;
  document_type: string;
  date?: string;
  amount?: number;
  category?: string;
  merchant?: string;
  drive_url?: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading: boolean;
  error?: string | null;
  processingTime?: number;
  totalResults?: number;
  onClose: () => void;
}

export function SearchResults({
  results,
  query,
  isLoading,
  error,
  processingTime,
  totalResults,
  onClose,
}: SearchResultsProps) {
  const { currentBusiness } = useBusiness();

  const formatAmount = (amount?: number) => {
    if (!amount) return null;
    return formatCurrency(amount, currentBusiness?.currency);
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const stripMarkdown = (text: string) => {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, "$1") // Remove bold **text**
      .replace(/\*(.*?)\*/g, "$1") // Remove italic *text*
      .replace(/`(.*?)`/g, "$1") // Remove code `text`
      .replace(/#{1,6}\s?/g, "") // Remove headers
      .replace(/\[(.*?)\]\(.*?\)/g, "$1") // Remove links [text](url)
      .replace(/---.*?---/g, "") // Remove --- Page X ---
      .replace(/\n+/g, " ") // Replace newlines with spaces
      .replace(/\s+/g, " ") // Normalize whitespace
      .trim();
  };

  const getDocumentTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "receipt":
      case "expense":
        return "🧾";
      case "invoice":
        return "📄";
      case "statement":
        return "📊";
      default:
        return "📋";
    }
  };

  if (error) {
    return (
      <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg mt-1 z-50">
        <div className="p-4">
          <div className="text-center">
            <div className="text-red-400 mb-2">⚠️</div>
            <p className="text-sm text-red-600 font-medium mb-1">
              Search Error
            </p>
            <p className="text-xs text-gray-600">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Refresh page
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg mt-1 z-50">
        <div className="p-4">
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-sm text-gray-600">
              Searching documents...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!results.length && query) {
    return (
      <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg mt-1 z-50">
        <div className="p-4">
          <div className="text-center">
            <div className="text-gray-400 mb-2">🔍</div>
            <p className="text-sm text-gray-600">
              No documents found for "{query}"
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Try different keywords or check if documents are uploaded
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!query || !results.length) {
    return null;
  }

  return (
    <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-md shadow-lg mt-1 z-50 max-w-2xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-900">
            {totalResults || results.length} result
            {(totalResults || results.length) !== 1 ? "s" : ""} for "{query}"
          </span>
          {processingTime && (
            <span className="text-xs text-gray-400">
              ({(processingTime * 1000).toFixed(0)}ms)
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-sm"
        >
          ✕
        </button>
      </div>

      {/* Results */}
      <div className="max-h-96 overflow-y-auto">
        {results.map((result) => (
          <div
            key={result.id}
            className="px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer group"
            onClick={() =>
              result.drive_url && window.open(result.drive_url, "_blank")
            }
          >
            <div className="flex items-start space-x-3">
              {/* Document Icon */}
              <div className="flex-shrink-0 text-lg">
                {getDocumentTypeIcon(result.document_type)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                {/* Title Row */}
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {result.document_type.replace("_", " ")}
                    </span>
                    {result.drive_url && (
                      <ExternalLinkIcon className="h-3 w-3 text-gray-400 group-hover:text-blue-500" />
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {(result.score * 100).toFixed(0)}% match
                  </span>
                </div>

                {/* Metadata Row */}
                <div className="flex items-center space-x-4 mb-2 text-xs text-gray-500">
                  {result.date && (
                    <div className="flex items-center space-x-1">
                      <CalendarIcon className="h-3 w-3" />
                      <span>{formatDate(result.date)}</span>
                    </div>
                  )}
                  {result.amount && (
                    <div className="flex items-center space-x-1">
                      <DollarSignIcon className="h-3 w-3" />
                      <span className="font-medium">
                        {formatAmount(result.amount)}
                      </span>
                    </div>
                  )}
                  {result.category && (
                    <div className="flex items-center space-x-1">
                      <TagIcon className="h-3 w-3" />
                      <span>{result.category}</span>
                    </div>
                  )}
                  {result.merchant && (
                    <div className="flex items-center space-x-1">
                      <BuildingIcon className="h-3 w-3" />
                      <span>{result.merchant}</span>
                    </div>
                  )}
                </div>

                {/* Content Preview */}
                <p className="text-sm text-gray-600 line-clamp-2">
                  {stripMarkdown(result.content)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-500 text-center">
          Powered by RAG semantic search
        </p>
      </div>
    </div>
  );
}
