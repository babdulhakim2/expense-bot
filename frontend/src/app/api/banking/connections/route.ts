import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";
import { getServerSession } from "next-auth/next";
import { NextResponse } from "next/server";

const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL;

export async function GET(request: Request) {
  const session = await getServerSession(authOptions) as any; // eslint-disable-line @typescript-eslint/no-explicit-any
  const { searchParams } = new URL(request.url);
  const businessId = searchParams.get("businessId");

  try {
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    if (!businessId) {
      return NextResponse.json(
        { error: "Business ID is required" },
        { status: 400 }
      );
    }

    // Call Flask backend to get connections
    const response = await fetch(
      `${FLASK_API_URL}/api/banking/connections?business_id=${businessId}`,
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to fetch bank connections");
    }

    return NextResponse.json({
      connections: data.connections || [],
    });
  } catch (error) {
    console.error("Error fetching bank connections:", error);
    return NextResponse.json(
      { error: "Failed to fetch bank connections" },
      { status: 500 }
    );
  }
}
