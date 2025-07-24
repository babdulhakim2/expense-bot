import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";

export const maxDuration = 250; 
export const dynamic = 'force-dynamic';

const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL;

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  try {
    // Forward the FormData directly to Flask
    const formData = await request.formData();
    
    // Validate required fields
    const file = formData.get('file');
    const businessId = formData.get('businessId');

    if (!file || !businessId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Forward to Flask backend
    const response = await fetch(`${FLASK_API_URL}/api/upload`, {
      method: 'POST',
      body: formData, // Forward the entire FormData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to process file');
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error: any) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to process file' },
      { status: 500 }
    );
  }
} 