import {
  collection,
  doc,
  getDocs,
  setDoc,
  updateDoc,
  getDoc,
  query,
  where,
  orderBy,
} from "firebase/firestore";
import { db } from "@/lib/firebase/firebase-config";

export type GoogleDriveConfig = {
  accessToken?: string;
  refreshToken?: string;
  scope?: string[];
  inputFolderPath?: string;
  outputFolderPath?: string;
  inputFolderId?: string;
  outputFolderId?: string;
  connectedAt?: Date;
  email?: string;
};

export type Business = {
  id: string;
  name: string;
  type: string;
  location?: string;
  businessNumber?: string;
  currency?: string;
  createdAt: Date;
  updatedAt: Date;
  userId: string;
  primaryEmail: string;
  googleDrive?: GoogleDriveConfig;
};

export type BusinessUser = {
  id: string;
  name: string;
  email: string;
  businessId: string; // Reference to the business this user belongs to
  role: "owner" | "admin" | "member";
  joinedAt: Date;
};

// Add new interfaces for the different types of data
interface AIAction {
  id: string;
  type: string;
  actionData: Record<string, unknown>;
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
  direction: "inbound" | "outbound";
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
  // Overloaded method for business context (takes object parameter)
  static async createBusiness(data: {
    name: string;
    type: string;
    location?: string;
    currency?: string;
    businessNumber?: string;
    userId: string;
    primaryEmail: string;
  }): Promise<Business>;
  // Legacy method (takes separate parameters)
  static async createBusiness(
    userId: string,
    userEmail: string,
    data: Omit<
      Business,
      "id" | "createdAt" | "updatedAt" | "userId" | "primaryEmail"
    >
  ): Promise<Business>;

  static async createBusiness(
    userIdOrData:
      | string
      | {
          name: string;
          type: string;
          location?: string;
          currency?: string;
          businessNumber?: string;
          userId: string;
          primaryEmail: string;
        },
    userEmail?: string,
    legacyData?: Omit<
      Business,
      "id" | "createdAt" | "updatedAt" | "userId" | "primaryEmail"
    >
  ): Promise<Business> {
    try {
      const businessRef = doc(collection(db, "businesses"));

      let businessData: Omit<Business, "createdAt" | "updatedAt"> & {
        createdAt: Date;
        updatedAt: Date;
      };

      // Handle both call patterns
      if (typeof userIdOrData === "string") {
        businessData = {
          id: businessRef.id,
          name: legacyData?.name || "",
          type: legacyData?.type || "",
          location: legacyData?.location || "",
          currency: legacyData?.currency || "GBP",
          businessNumber: legacyData?.businessNumber || "",
          userId: userIdOrData, // Store as userId for consistency
          primaryEmail: userEmail!,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
      } else {
        businessData = {
          id: businessRef.id,
          name: userIdOrData.name,
          type: userIdOrData.type,
          location: userIdOrData.location || "",
          currency: userIdOrData.currency || "GBP",
          businessNumber: userIdOrData.businessNumber || "",
          userId: userIdOrData.userId,
          primaryEmail: userIdOrData.primaryEmail,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
      }

      await setDoc(businessRef, businessData);
      console.log("Business created successfully with ID:", businessRef.id);

      const newBusiness: Business = {
        ...businessData,
        createdAt: businessData.createdAt,
        updatedAt: businessData.updatedAt,
      };


      return newBusiness;
    } catch (error) {
      console.error("Error creating business:", error);
      throw error;
    }
  }

  static async getUserBusinesses(userId: string): Promise<Business[]> {
    try {
      // Query all businesses where user is owner or member
      const businessesQuery = query(
        collection(db, "businesses"),
        where("userId", "==", userId),
        orderBy("createdAt", "desc")
      );

      const businessSnapshot = await getDocs(businessesQuery);

      const businesses: Business[] = [];

      for (const doc of businessSnapshot.docs) {
        const data = doc.data();
        businesses.push({
          id: data.id,
          name: data.name,
          type: data.type,
          location: data.location || "",
          currency: data.currency || "",
          businessNumber: data.businessNumber || "",
          createdAt: data.createdAt.toDate(),
          updatedAt: data.updatedAt.toDate(),
          userId: data.userId,
          primaryEmail: data.primaryEmail,
        });
      }

      return businesses;
    } catch (error) {
      console.error("Error getting user businesses:", error);
      return [];
    }
  }


  static async getBusiness(businessId: string): Promise<Business> {
    const businessRef = doc(db, "businesses", businessId);
    const businessDoc = await getDoc(businessRef);

    if (!businessDoc.exists()) {
      throw new Error("Business not found");
    }

    const data = businessDoc.data();
    const createdAt = data.createdAt?.toDate?.() || new Date();
    const updatedAt = data.updatedAt?.toDate?.() || new Date();

    return {
      id: businessDoc.id, // Use the document ID
      name: data.name || "",
      type: data.type || "",
      location: data.location || "",
      currency: data.currency || "",
      businessNumber: data.businessNumber || "",
      createdAt,
      updatedAt,
      userId: data.userId || "",
      primaryEmail: data.primaryEmail || "",
    };
  }

  static async updateBusiness(
    businessId: string,
    data: Partial<Omit<Business, "id" | "createdAt" | "" | "primaryEmail">>
  ) {
    const businessRef = doc(db, "businesses", businessId);

    // Filter out undefined values
    const cleanData = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== undefined && value !== "") {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, unknown>);

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
        collection(db, "businesses", businessId, "actions"),
        orderBy("created_at", "desc")
      );

      const snapshot = await getDocs(actionsQuery);
      console.log("Snapshot:", snapshot);
      return snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
        } as AIAction;
      });
    } catch (error) {
      console.error("Error fetching business actions:", error);
      throw error;
    }
  }

  static async getBusinessFolders(businessId: string): Promise<Folder[]> {
    try {
      const foldersQuery = query(
        collection(db, "businesses", businessId, "folders"),
        orderBy("createdAt", "desc")
      );

      const snapshot = await getDocs(foldersQuery);
      return snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
          updatedAt: data.updatedAt?.toDate?.() || new Date(data.updatedAt),
        } as Folder;
      });
    } catch (error) {
      console.error("Error fetching business folders:", error);
      throw error;
    }
  }

  static async getBusinessMessages(businessId: string): Promise<Message[]> {
    try {
      const messagesQuery = query(
        collection(db, "businesses", businessId, "messages"),
        orderBy("timestamp", "desc")
      );

      const snapshot = await getDocs(messagesQuery);
      return snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          timestamp: data.timestamp?.toDate?.() || new Date(data.timestamp),
        } as Message;
      });
    } catch (error) {
      console.error("Error fetching business messages:", error);
      throw error;
    }
  }

  static async getBusinessSpreadsheets(
    businessId: string
  ): Promise<Spreadsheet[]> {
    try {
      const spreadsheetsQuery = query(
        collection(db, "businesses", businessId, "spreadsheets"),
        orderBy("createdAt", "desc")
      );

      const snapshot = await getDocs(spreadsheetsQuery);
      return snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
          updatedAt: data.updatedAt?.toDate?.() || new Date(data.updatedAt),
        } as Spreadsheet;
      });
    } catch (error) {
      console.error("Error fetching business spreadsheets:", error);
      throw error;
    }
  }

  static async getBusinessTransactions(
    businessId: string
  ): Promise<Transaction[]> {
    try {
      const transactionsQuery = query(
        collection(db, "businesses", businessId, "transactions"),
        orderBy("date", "desc")
      );

      const snapshot = await getDocs(transactionsQuery);
      return snapshot.docs.map((doc) => {
        const data = doc.data();
        return {
          id: doc.id,
          ...data,
          createdAt: data.createdAt?.toDate?.() || new Date(data.createdAt),
        } as Transaction;
      });
    } catch (error) {
      console.error("Error fetching business transactions:", error);
      throw error;
    }
  }

  static async updateGoogleDriveConfig(
    businessId: string,
    config: GoogleDriveConfig
  ): Promise<void> {
    try {
      const businessRef = doc(db, "businesses", businessId);
      await updateDoc(businessRef, {
        googleDrive: {
          ...config,
          connectedAt: config.connectedAt || new Date(),
        },
        updatedAt: new Date(),
      });
    } catch (error) {
      console.error("Error updating Google Drive config:", error);
      throw error;
    }
  }

  static async removeGoogleDriveConfig(businessId: string): Promise<void> {
    try {
      const businessRef = doc(db, "businesses", businessId);
      await updateDoc(businessRef, {
        googleDrive: null,
        updatedAt: new Date(),
      });
    } catch (error) {
      console.error("Error removing Google Drive config:", error);
      throw error;
    }
  }
}
