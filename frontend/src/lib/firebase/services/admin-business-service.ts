import { adminDb } from '@/lib/firebase/firebase-admin';
import type { Business } from './business-service';

export class AdminBusinessService {
  static async getUserBusinesses(userId: string): Promise<Business[]> {
    try {
      const snapshot = await adminDb
        .collection('businesses')
        .where('userId', '==', userId)
        .orderBy('createdAt', 'desc')
        .get();

      const businesses: Business[] = [];

      for (const doc of snapshot.docs) {
        const data = doc.data();
        businesses.push({
          id: doc.id,
          name: data.name || '',
          type: data.type || '',
          location: data.location || '',
          currency: data.currency || 'GBP',
          businessNumber: data.businessNumber || '',
          createdAt: data.createdAt?.toDate() || new Date(),
          updatedAt: data.updatedAt?.toDate() || new Date(),
          userId: data.userId || '',
          primaryEmail: data.primaryEmail || '',
        });
      }

      return businesses;
    } catch (error) {
      console.error('Error getting user businesses with Admin SDK:', error);
      return [];
    }
  }

  static async getBusiness(businessId: string): Promise<Business | null> {
    try {
      const doc = await adminDb.collection('businesses').doc(businessId).get();
      
      if (!doc.exists) {
        return null;
      }

      const data = doc.data()!;
      return {
        id: doc.id,
        name: data.name || '',
        type: data.type || '',
        location: data.location || '',
        currency: data.currency || 'GBP',
        businessNumber: data.businessNumber || '',
        createdAt: data.createdAt?.toDate() || new Date(),
        updatedAt: data.updatedAt?.toDate() || new Date(),
        userId: data.userId || '',
        primaryEmail: data.primaryEmail || '',
      };
    } catch (error) {
      console.error('Error getting business with Admin SDK:', error);
      return null;
    }
  }
}