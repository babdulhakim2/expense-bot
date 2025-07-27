import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";

const GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";
const REQUIRED_SCOPES = [
  "https://www.googleapis.com/auth/drive.file",
  "https://www.googleapis.com/auth/drive.metadata.readonly",
  "https://www.googleapis.com/auth/spreadsheets",
];

export async function GET(request: NextRequest) {
  try {
    const session = (await getServerSession(authOptions)) as any;
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const businessId = searchParams.get("businessId");
    const redirectUrl = searchParams.get("redirectUrl") || "/setup";

    if (!businessId) {
      return NextResponse.json({ error: "Business ID required" }, { status: 400 });
    }

    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
    const baseUrl = process.env.NEXTAUTH_URL || `${request.nextUrl.protocol}//${request.nextUrl.host}`;

    if (!clientId || !clientSecret) {
      console.log("Google OAuth not configured. Client ID:", !!clientId, "Client Secret:", !!clientSecret);
      return NextResponse.json({ 
        error: "Google OAuth not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your environment variables." 
      }, { status: 500 });
    }

    const state = Buffer.from(JSON.stringify({ businessId, redirectUrl })).toString('base64');
    
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: `${baseUrl}/api/auth/google-drive/callback`,
      response_type: "code",
      scope: REQUIRED_SCOPES.join(" "),
      access_type: "offline",
      prompt: "consent",
      state,
    });

    const authUrl = `${GOOGLE_OAUTH_URL}?${params.toString()}`;
    
    return NextResponse.json({ authUrl });
  } catch (error) {
    console.error("Error generating Google Drive auth URL:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}