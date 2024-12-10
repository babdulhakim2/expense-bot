import { doc, setDoc } from 'firebase/firestore';
import { db } from '@/lib/firebase/firebase';

export type User = {
  id: string;
  name: string;
  email: string;
  phoneNumber?: string;
  createdAt: Date;
  updatedAt: Date;
};

export class UserService {
  static async createOrUpdateUser(userData: Partial<User> & { id: string }) {
    const userRef = doc(db, 'users', userData.id);
    const data = {
      ...userData,
      updatedAt: new Date(),
    };

    await setDoc(userRef, data, { merge: true });
    return data;
  }
} 