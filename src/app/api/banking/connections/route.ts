import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { BusinessService } from '@/lib/firebase/services/business-service';

const FLASK_API_URL = process.env.FLASK_API_URL || 'http://127.0.0.1:9004';

export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  const { searchParams } = new URL(request.url);
  const businessId = searchParams.get('businessId');

  try {
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    if (!businessId) {
      return NextResponse.json(
        { error: 'Business ID is required' },
        { status: 400 }
      );
    }

    // Call Flask backend to get connections
    const response = await fetch(`${FLASK_API_URL}/api/banking/connections?business_id=${businessId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to fetch bank connections');
    }

    return NextResponse.json({
      connections: data.connections || []
    });

  } catch (error) {
    console.error('Error fetching bank connections:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bank connections' },
      { status: 500 }
    );
  }
} 