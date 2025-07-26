import { doc, setDoc, getDoc } from 'firebase/firestore';
import { db } from '@/lib/firebase/firebase-config';

export type User = {
  id: string;
  name: string;
  email: string;
  phoneNumber?: string;
  role?: string;
  businessId?: string;
  createdAt: Date;
  updatedAt: Date;
};

export class UserService {


  static async createOrUpdateUser(userData: Partial<User> & { id: string }) {
    const userRef = doc(db, 'users', userData.id);
    
    // Get existing user data first
    const existingUser = await this.getUser(userData.id);
    
    const data = {
      ...existingUser, 
      ...userData, 
      createdAt: existingUser?.createdAt || new Date(),
      updatedAt: new Date(),
    };

    await setDoc(userRef, data, { merge: true });
    return data;
  }

  static async getUser(userId: string): Promise<User | null> {
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      return null;
    }

    const data = userDoc.data();
    return {
      ...data,
      createdAt: data.createdAt?.toDate(),
      updatedAt: data.updatedAt?.toDate(),
    } as User;
  }
} 