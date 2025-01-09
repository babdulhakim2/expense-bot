import { collection, doc, getDocs, setDoc, DocumentData, updateDoc, getDoc, query, where, orderBy } from 'firebase/firestore';
import { db } from '@/lib/firebase/firebase';

export type Business = {
  id: string;
  name: string;
  type: string;
  location?: string;
  businessNumber?: string;
  currency?: string;
  createdAt: Date;
  updatedAt: Date;
  ownerId: string;
  ownerEmail: string;
};

export type BusinessUser = {
  id: string;
  name: string;
  email: string;
  businessId: string;  // Reference to the business this user belongs to
  role: 'owner' | 'admin' | 'member';
  joinedAt: Date;
};

// Add new interfaces for the different types of data
interface AIAction {
  id: string;
  type: string;
  actionData: any;
  createdAt: Date;
  relatedId?: string;
  businessId: string;
}

interface Folder {
  id: string;
  name: string;
  type: string;
  drive_folder_id: string;
  url: string;
  businessId: string;
  createdAt: Date;
  updatedAt: Date;
  status: string;
  action_id?: string;
}

interface Message {
  id: string;
  direction: 'inbound' | 'outbound';
  content: string;
  type: string;
  timestamp: Date;
  businessId: string;
  related_message_id?: string;
  error_details?: string;
}

interface Spreadsheet {
  id: string;
  name: string;
  drive_id: string;
  url: string;
  type: string;
  businessId: string;
  createdAt: Date;
  updatedAt: Date;
  year: string;
  month: string;
}

interface Transaction {
  id: string;
  date: string;
  amount: number;
  description: string;
  category: string;
  payment_method: string;
  merchant: string;
  currency: string;
  businessId: string;
  createdAt: Date;
  spreadsheet_id: string;
}

export class BusinessService {
  static async createBusiness(userId: string, userEmail: string, data: Omit<Business, 'id' | 'createdAt' | 'updatedAt' | 'ownerId' | 'ownerEmail'>) {
    const businessRef = doc(collection(db, 'businesses'));
    const businessData = {
      id: businessRef.id,
      ...data,
      ownerId: userId,
      ownerEmail: userEmail,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    await setDoc(businessRef, businessData);

    // Create user document
    const userRef = doc(db, 'users', userId);
    await setDoc(userRef, {
      id: userId,
      email: userEmail,
      name: data.name,
      businessId: businessRef.id,
      role: 'owner',
      joinedAt: new Date()
    });

    return businessData;
  }

  static async getUserBusinesses(userId: string): Promise<Business[]> {
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      return [];
    }

    const userData = userDoc.data() as BusinessUser;
    if (!userData.businessId) {
      return [];
    }

    const business = await this.getBusiness(userData.businessId);
    return [business];
  }

  static async getBusinessByUserEmail(email: string | null | undefined): Promise<Business | null> {
    if (!email) return null;
    try {
      const usersQuery = query(
        collection(db, 'users'),
        where('email', '==', email)
      );
      const userSnapshot = await getDocs(usersQuery);

      if (!userSnapshot.empty) {
        const userData = userSnapshot.docs[0].data() as BusinessUser;
        if (userData.businessId) {
          return await this.getBusiness(userData.businessId);
        }
      }

      return null;
    } catch (error) {
      console.error('Error getting business by user email:', error);
      throw error;
    }
  }

  static async getBusiness(businessId: string): Promise<Business> {
    const businessRef = doc(db, 'businesses', businessId);
    const businessDoc = await getDoc(businessRef);
    
    if (!businessDoc.exists()) {
      throw new Error('Business not found');
    }

    const data = businessDoc.data();
    return {
      id: data.id,
      name: data.name,
      type: data.type,
      location: data.location || '',
      currency: data.currency || '',
      businessNumber: data.businessNumber || '',
      createdAt: data.createdAt.toDate(),
      updatedAt: data.updatedAt.toDate(),
      ownerId: data.ownerId,
      ownerEmail: data.ownerEmail,
    };
  }

  static async updateBusiness(businessId: string, data: Partial<Omit<Business, 'id' | 'createdAt' | 'ownerId' | 'ownerEmail'>>) {
    const businessRef = doc(db, 'businesses', businessId);
    
    // Filter out undefined values
    const cleanData = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== undefined && value !== '') {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, any>);

    const updateData = {
      ...cleanData,
      updatedAt: new Date(),
    };

    await updateDoc(businessRef, updateData);
    return updateData;
  }

  static async getBusinessActions(businessId: string): Promise<AIAction[]> {
    try {
      const actionsQuery = query(
        collection(db, 'businesses', businessId, 'actions'),
        orderBy('created_at', 'desc')
      );
      
      const snapshot = await getDocs(actionsQuery);
      console.log('Snapshot:', snapshot);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt)
        } as AIAction;
      });
    } catch (error) {
      console.error('Error fetching business actions:', error);
      throw error;
    }
  }

  static async getBusinessFolders(businessId: string): Promise<Folder[]> {
    try {
      const foldersQuery = query(
        collection(db, 'businesses', businessId, 'folders'),
        orderBy('createdAt', 'desc')
      );
      
      const snapshot = await getDocs(foldersQuery);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
          updatedAt: data.updatedAt?.toDate?.() || new Date(data.updatedAt)
        } as Folder;
      });
    } catch (error) {
      console.error('Error fetching business folders:', error);
      throw error;
    }
  }

  static async getBusinessMessages(businessId: string): Promise<Message[]> {
    try {
      const messagesQuery = query(
        collection(db, 'businesses', businessId, 'messages'),
        orderBy('timestamp', 'desc')
      );
      
      const snapshot = await getDocs(messagesQuery);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          timestamp: data.timestamp?.toDate?.() || new Date(data.timestamp)
        } as Message;
      });
    } catch (error) {
      console.error('Error fetching business messages:', error);
      throw error;
    }
  }

  static async getBusinessSpreadsheets(businessId: string): Promise<Spreadsheet[]> {
    try {
      const spreadsheetsQuery = query(
        collection(db, 'businesses', businessId, 'spreadsheets'),
        orderBy('createdAt', 'desc')
      );
      
      const snapshot = await getDocs(spreadsheetsQuery);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
          updatedAt: data.updatedAt?.toDate?.() || new Date(data.updatedAt)
        } as Spreadsheet;
      });
    } catch (error) {
      console.error('Error fetching business spreadsheets:', error);
      throw error;
    }
  }

  static async getBusinessTransactions(businessId: string): Promise<Transaction[]> {
    try {
      const transactionsQuery = query(
        collection(db, 'businesses', businessId, 'transactions'),
        orderBy('date', 'desc')
      );
      
      const snapshot = await getDocs(transactionsQuery);
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt)
        } as Transaction;
      });
    } catch (error) {
      console.error('Error fetching business transactions:', error);
      throw error;
    }
  }
} 