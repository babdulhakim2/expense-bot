import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth/next";
import { db } from '@/lib/firebase/firebase';
import { authOptions } from "@/lib/auth";
import { collection, query, limit, getDocs, doc } from 'firebase/firestore';
import { BusinessService, type Business } from '@/lib/firebase/services/business-service';

export async function GET(request: Request) {
  const session = await getServerSession(authOptions);

  try {
    const user = session?.user;

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 400 });
    }

    // Get first business for user using collection reference
    const userBusinesses = await BusinessService.getUserBusinesses(session.user.id);
    // const businessesRef = collection(db, 'users', user.id, 'businesses');
    // const businesses = await doc(db, 'users', user.id, 'businesses');
    console.log('businesses:', userBusinesses);
    // console.log('businessesRef:', businessesRef);
    // const businessesQuery = query(businessesRef, limit(1));
    // const businessesSnapshot = await getDocs(businessesQuery);

    if (!userBusinesses) {
      return NextResponse.json({ error: 'No business found' }, { status: 404 });
    }

    const business = userBusinesses[0];
    return NextResponse.json({
      business_id: business.id,
      ...business
    });

  } catch (error) {
    console.error('Error fetching business:', error);
    return NextResponse.json(
      { error: 'Failed to fetch business' },
      { status: 500 }
    );
  }
} 