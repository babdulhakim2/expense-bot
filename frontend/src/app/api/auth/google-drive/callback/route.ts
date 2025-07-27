import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";
import { BusinessService } from "@/lib/firebase/services/business-service";

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";

export async function GET(request: NextRequest) {
  try {
    
    const session = (await getServerSession(authOptions)) as any;
    if (!session?.user) {
      return NextResponse.redirect(new URL("/", request.url));
    }

    const { searchParams } = new URL(request.url);
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const error = searchParams.get("error");

    if (error) {
      console.error("Google OAuth error:", error);
      return NextResponse.redirect(new URL("/setup?error=google_auth_failed", request.url));
    }

    if (!code || !state) {
      return NextResponse.redirect(new URL("/setup?error=missing_params", request.url));
    }

    // Decode state to get businessId and redirectUrl
    let businessId: string;
    let redirectUrl: string;
    try {
      const decodedState = JSON.parse(Buffer.from(state, 'base64').toString());
      businessId = decodedState.businessId;
      redirectUrl = decodedState.redirectUrl || "/setup";
    } catch {
      return NextResponse.redirect(new URL("/setup?error=invalid_state", request.url));
    }

    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
    const baseUrl = process.env.NEXTAUTH_URL || `${request.nextUrl.protocol}//${request.nextUrl.host}`;

    if (!clientId || !clientSecret) {
      return NextResponse.redirect(new URL("/setup?error=config_missing", request.url));
    }

    // Exchange code for tokens
    const tokenResponse = await fetch(GOOGLE_TOKEN_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        code,
        grant_type: "authorization_code",
        redirect_uri: `${baseUrl}/api/auth/google-drive/callback`,
      }),
    });

    if (!tokenResponse.ok) {
      console.error("Failed to exchange code for tokens:", await tokenResponse.text());
      return NextResponse.redirect(new URL("/setup?error=token_exchange_failed", request.url));
    }

    const tokens = await tokenResponse.json();

    // Get user info to verify the token and get email
    const userInfoResponse = await fetch(
      `https://www.googleapis.com/oauth2/v2/userinfo?access_token=${tokens.access_token}`
    );

    if (!userInfoResponse.ok) {
      console.error("Failed to get user info:", await userInfoResponse.text());
      return NextResponse.redirect(new URL("/setup?error=user_info_failed", request.url));
    }

    const userInfo = await userInfoResponse.json();

    // Save Google Drive config to business
    await BusinessService.updateGoogleDriveConfig(businessId, {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      scope: tokens.scope?.split(" ") || [],
      email: userInfo.email,
      connectedAt: new Date(),
    });

    return NextResponse.redirect(new URL(`${redirectUrl}?google_drive=connected`, request.url));
  } catch (error) {
    console.error("Error in Google Drive callback:", error);
    return NextResponse.redirect(new URL("/setup?error=callback_failed", request.url));
  }
}