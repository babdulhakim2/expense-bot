import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";

export const maxDuration = 60;
export const dynamic = "force-dynamic";

interface SearchRequest {
  query: string;
  business_id: string;
  limit?: number;
  filters?: Record<string, any>;
  enhance_query?: boolean;
}

interface SearchResult {
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

interface SearchResponse {
  success: boolean;
  query: string;
  results: SearchResult[];
  total_results: number;
  processing_time: number;
  search_method: string;
}

export async function POST(request: Request) {
  const session = (await getServerSession(authOptions)) as any;

  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body: SearchRequest = await request.json();

    // Validate required fields
    if (!body.query?.trim()) {
      return NextResponse.json({ error: "Query is required" }, { status: 400 });
    }

    if (!body.business_id?.trim()) {
      return NextResponse.json(
        { error: "Business ID is required" },
        { status: 400 }
      );
    }

    // Prepare search request
    const searchRequest = {
      query: body.query.trim(),
      business_id: body.business_id.trim(),
      limit: Math.min(body.limit || 10, 20), // Cap at 20 for frontend
      filters: body.filters || {},
      enhance_query: body.enhance_query !== false, // Default to true
    };

    console.log(
      `[Search] Query: "${searchRequest.query}" for business: ${searchRequest.business_id}`
    );

 
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/search`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(searchRequest),
      }
    );

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ message: "Search service unavailable" }));
      console.error("[Search] Backend error:", error);

      return NextResponse.json(
        {
          error: "Search failed",
          message: error.message || "Search service temporarily unavailable",
          success: false,
        },
        { status: response.status }
      );
    }

    const data: SearchResponse = await response.json();
    console.log("[Search] Backend response:", data);

    console.log(
      `[Search] Found ${data.total_results} results in ${data.processing_time}s`
    );

    // Return search results to frontend
    return NextResponse.json({
      success: true,
      query: data.query,
      results: data.results,
      total_results: data.total_results,
      processing_time: data.processing_time,
      search_method: data.search_method,
    });
  } catch (error) {
    console.error("[Search] Error:", error);
    return NextResponse.json(
      {
        error: "Search failed",
        message:
          error instanceof Error ? error.message : "Unknown error occurred",
        success: false,
      },
      { status: 500 }
    );
  }
}
