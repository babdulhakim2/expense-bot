"use server";

import { getServerSession } from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";
import { AdminBusinessService } from "@/lib/firebase/services/admin-business-service";
import type { Business } from "@/lib/firebase/services/business-service";
import { adminDb } from "@/lib/firebase/firebase-admin";

export async function getServerBusinesses(): Promise<Business[]> {
  try {
    const session = (await getServerSession(authOptions)) as any; // eslint-disable-line @typescript-eslint/no-explicit-any
    console.log("Session:", session);

    if (!session?.user) {
      return [];
    }

    const userId = session.user?.firestoreUserId || session.user?.id;

    if (!userId) {
      console.error("No user ID found in session");
      return [];
    }

    // Use Admin SDK to get businesses (bypasses security rules)
    const businesses = await AdminBusinessService.getUserBusinesses(userId);
    console.log("Found businesses:", businesses.length);
    return businesses;
  } catch (error) {
    console.error("Error getting server businesses:", error);
    return [];
  }
}

export async function getServerUser() {
  try {
    const session = (await getServerSession(authOptions)) as any;

    if (!session?.user) {
      return null;
    }

    const userId = session.user?.firestoreUserId || session.user?.id;

    if (!userId) {
      return null;
    }

    const user = await adminDb.collection("users").doc(userId).get();
    if (!user.exists) {
      return null;
    }
    const userData = user.data();
    if (!userData) {
      return null;
    }
    // Return user data with ID
    const userWithId = {
      id: user.id,
      ...userData,
    };

    console.log("Found user:", user);
    return user;
  } catch (error) {
    return null;
  }
}
