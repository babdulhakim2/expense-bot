"use client";

import { useBusiness } from "@/app/providers/BusinessProvider";
import {
  SearchResult,
  SearchResults,
} from "@/components/dashboard/search/search-results";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LogOutIcon,
  SearchIcon,
  SettingsIcon,
  UserIcon
} from "lucide-react";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export function DashboardHeader() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchStats, setSearchStats] = useState<{
    processingTime?: number;
    totalResults?: number;
  }>({});

  const { data: session } = useSession();
  const router = useRouter();
  const { currentBusiness } = useBusiness();
  const searchRef = useRef<HTMLDivElement>(null);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  const getUserInitials = () => {
    if (session?.user?.name) {
      return session.user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);
    }
    if (session?.user?.email) {
      return session.user.email[0].toUpperCase();
    }
    return "U";
  };

  const handleLogout = async () => {
    await signOut({ redirect: true, callbackUrl: "/" });
  };

  // Search functionality
  const performSearch = async (query: string) => {
    if (!query.trim() || !currentBusiness?.id) {
      setSearchResults([]);
      setShowResults(false);
      setSearchError(null);
      return;
    }

    setIsSearching(true);
    setShowResults(true);
    setSearchError(null);

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
          business_id: currentBusiness.id,
          limit: 10,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Search failed (${response.status})`);
      }

      if (!data.success) {
        throw new Error(data.error || "Search request was not successful");
      }

      setSearchResults(data.results || []);
      setSearchStats({
        processingTime: data.processing_time,
        totalResults: data.total_results,
      });
    } catch (error) {
      console.error("Search error:", error);
      setSearchResults([]);
      setSearchStats({});

      // Set user-friendly error message
      if (error instanceof Error) {
        if (error.message.includes("RAG service not available")) {
          setSearchError(
            "Search service is currently unavailable. Please try again later."
          );
        } else if (error.message.includes("503")) {
          setSearchError(
            "Search service is temporarily down. Please try again in a few minutes."
          );
        } else if (error.message.includes("500")) {
          setSearchError("Internal server error occurred. Please try again.");
        } else if (
          error.message.includes("NetworkError") ||
          error.message.includes("fetch")
        ) {
          setSearchError(
            "Network error. Please check your connection and try again."
          );
        } else {
          setSearchError("Search failed. Please try again.");
        }
      } else {
        setSearchError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    setSearchError(null); // Clear errors when typing

    // Clear existing timeout
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    // Debounce search
    if (query.trim()) {
      searchTimeout.current = setTimeout(() => {
        performSearch(query);
      }, 500);
    } else {
      setSearchResults([]);
      setShowResults(false);
      setSearchError(null);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }
    performSearch(searchQuery);
  };

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(event.target as Node)
      ) {
        setShowResults(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
    };
  }, []);

  return (
    <header className="h-16 border-b border-gray-200 bg-white px-6 flex items-center justify-between">
      <div className="flex items-center flex-1">
        <div className="relative w-96" ref={searchRef}>
          <form onSubmit={handleSearchSubmit}>
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents and receipts..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => searchQuery && setShowResults(true)}
            />
          </form>

          {/* Search Results Dropdown */}
          {showResults && (
            <SearchResults
              results={searchResults}
              query={searchQuery}
              isLoading={isSearching}
              error={searchError}
              processingTime={searchStats.processingTime}
              totalResults={searchStats.totalResults}
              onClose={() => setShowResults(false)}
            />
          )}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="focus:outline-none">
              <Avatar className="h-8 w-8 cursor-pointer">
                <AvatarImage src={session?.user?.image || ""} />
                <AvatarFallback className="bg-gray-200 text-gray-600 text-sm">
                  {getUserInitials()}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">
                  {session?.user?.name || "User"}
                </p>
                <p className="text-xs text-gray-500">
                  {session?.user?.email || ""}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => router.push("/dashboard")}
              className="cursor-pointer"
            >
              <UserIcon className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => router.push("/dashboard/settings")}
              className="cursor-pointer"
            >
              <SettingsIcon className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="cursor-pointer text-red-600"
            >
              <LogOutIcon className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
