import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth/next";
import { db } from '@/lib/firebase/firebase';
import { authOptions } from "@/lib/auth";
import { doc, getDoc } from 'firebase/firestore';
import { BusinessService, type Business } from '@/lib/firebase/services/business-service';


const FLASK_API_URL = process.env.FLASK_API_URL || 'http://127.0.0.1:9004';

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);


  try {
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }


    const body = await request.json();
    const { business_id } = body;
    // const business = userBusinesses[0];
    console.log('business_id:', business_id);


    if (!business_id) {
      return NextResponse.json(
        { error: 'Business ID is required' },
        { status: 400 }
      );
    }

    // Call Flask backend
    const response = await fetch(`${FLASK_API_URL}/api/banking/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: session.user.id,
        business_id: business_id,
      }),
    });

    const data = await response.json();
    console.log('data:', data);

    if (!response.ok) {
      throw new Error(data.error || 'Failed to connect to banking service');
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Banking connect error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to banking service' },
      { status: 500 }
    );
  }
} 