import { collection, doc, getDocs, setDoc, DocumentData } from 'firebase/firestore';
import { db } from '@/lib/firebase/firebase';

export type Business = {
  id: string;
  name: string;
  type: string;
  createdAt: Date;
  updatedAt: Date;
};

export class BusinessService {
  static async createBusiness(userId: string, data: Omit<Business, 'id' | 'createdAt' | 'updatedAt'>) {
    const businessRef = doc(collection(db, 'users', userId, 'businesses'));
    const businessData = {
      id: businessRef.id,
      ...data,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    await setDoc(businessRef, businessData);
    return businessData;
  }

  static async getUserBusinesses(userId: string): Promise<Business[]> {
    const businessesRef = collection(db, 'users', userId, 'businesses');
    const querySnapshot = await getDocs(businessesRef);
    
    return querySnapshot.docs.map(doc => {
      const data = doc.data();
      return {
        ...data,
        createdAt: data.createdAt.toDate(),
        updatedAt: data.updatedAt.toDate(),
      } as Business;
    });
  }

  static convertFirestoreData(data: DocumentData): Business {
    return {
      id: data.id,
      name: data.name,
      type: data.type,
      createdAt: data.createdAt.toDate(),
      updatedAt: data.updatedAt.toDate(),
    };
  }
} 