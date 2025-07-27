"use client";

import {
  BusinessService,
  type Business,
} from "@/lib/firebase/services/business-service";
import { useSession } from "next-auth/react";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

type LoadingStates = {
  loading: boolean;
  creating: boolean;
  selecting: boolean;
  switching?: boolean;
  deleting?: boolean;
};

type BusinessContextType = {
  // State
  businesses: Business[];
  currentBusiness: Business | null;
  loadingStates: LoadingStates;
  hasBusinesses: boolean;
  isInitialized: boolean;

  // Actions
  addBusiness: (business: Business) => void;
  selectBusiness: (business: Business) => void;
  refreshBusinesses: () => Promise<void>;
  createAndSelectBusiness: (data: {
    name: string;
    type: string;
    location?: string;
  }) => Promise<Business>;
  getUserBusinesses: () => Promise<Business[]>;
};

const BusinessContext = createContext<BusinessContextType | undefined>(
  undefined
);

interface BusinessProviderProps {
  children: React.ReactNode;
  initialBusinesses?: Business[];
}

export function BusinessProvider({
  children,
  initialBusinesses,
}: BusinessProviderProps) {
  const { data: session } = useSession();
  const [businesses, setBusinesses] = useState<Business[]>(
    initialBusinesses || []
  );
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(
    initialBusinesses && initialBusinesses.length > 0
      ? initialBusinesses[0]
      : null
  );
  const [loadingStates, setLoadingStates] = useState<LoadingStates>({
    loading: !initialBusinesses, // Only load if no initial businesses provided
    creating: false,
    selecting: false,
  });
  const [isInitialized, setIsInitialized] = useState(!!initialBusinesses);

  // Computed values
  const hasBusinesses = businesses.length > 0;

  // Load businesses for the current user (only if no initial businesses provided)
  const loadBusinesses = useCallback(async () => {
    // Skip loading if we already have initial businesses
    if (initialBusinesses && initialBusinesses.length > 0) {
      return;
    }

    if (!session?.user?.email) {
      setIsInitialized(true);
      setLoadingStates((prev) => ({ ...prev, loading: false }));
      return;
    }

    setLoadingStates((prev) => ({ ...prev, loading: true }));

    // Try to get all businesses for this user
    const userBusinesses = await BusinessService.getUserBusinesses(
      (session.user as any).id
    ); // eslint-disable-line @typescript-eslint/no-explicit-any
    setBusinesses(userBusinesses);

    // Set current business to first one if none selected
    if (userBusinesses.length > 0 && !currentBusiness) {
      setCurrentBusiness(userBusinesses[0]);
    } else if (userBusinesses.length === 0) {
      setCurrentBusiness(null);
    }
  }, [
    session?.user?.email,
    (session?.user as any)?.id,
    initialBusinesses,
    currentBusiness,
  ]);

  // Initial load (only if no initial businesses)
  useEffect(() => {
    if (!initialBusinesses) {
      loadBusinesses();
    }
  }, [loadBusinesses, initialBusinesses]);

  const addBusiness = useCallback((business: Business) => {
    setBusinesses((prev) => [...prev, business]);
  }, []);

  const selectBusiness = useCallback(async (business: Business) => {
    try {
      setLoadingStates((prev) => ({ ...prev, selecting: true }));
      setCurrentBusiness(business);
    } catch (error) {
      console.error("Failed to select business:", error);
    } finally {
      setLoadingStates((prev) => ({ ...prev, selecting: false }));
    }
  }, []);

  const refreshBusinesses = useCallback(async () => {
    await loadBusinesses();
  }, [loadBusinesses]);

  const getUserBusinesses = useCallback(async (): Promise<Business[]> => {
    if (!(session?.user as any)?.id) return []; // eslint-disable-line @typescript-eslint/no-explicit-any
    try {
      // Use the Firestore user ID (which is same as Firebase Auth UID for consistency)
      const firestoreUserId =
        (session?.user as any)?.firestoreUserId || (session?.user as any)?.id; // eslint-disable-line @typescript-eslint/no-explicit-any
      return await BusinessService.getUserBusinesses(firestoreUserId);
    } catch (error) {
      console.error("Failed to get user businesses:", error);
      return [];
    }
  }, [(session?.user as any)?.id, (session?.user as any)?.firestoreUserId]); // eslint-disable-line @typescript-eslint/no-explicit-any

  const createAndSelectBusiness = useCallback(
    async (data: {
      name: string;
      type: string;
      location?: string;
    }): Promise<Business> => {
      if (!(session?.user as any)?.id || !session?.user?.email) {
        throw new Error("User session required");
      }

      try {
        setLoadingStates((prev) => ({ ...prev, creating: true }));

        // Use the Firestore user ID (which is same as Firebase Auth UID for consistency)
        const firestoreUserId =
          (session.user as any).firestoreUserId || (session.user as any).id; 
        // Create the business
        const newBusiness = await BusinessService.createBusiness({
          name: data.name,
          type: data.type,
          location: data.location || "",
          currency: "GBP", // Default currency
          userId: firestoreUserId, // Use Firestore user ID
          primaryEmail: session.user.email,
        });

        // Add to local state
        setBusinesses((prev) => [...prev, newBusiness]);
        setCurrentBusiness(newBusiness);

        return newBusiness;
      } catch (error) {
        console.error("Failed to create business:", error);
        throw error;
      } finally {
        setLoadingStates((prev) => ({ ...prev, creating: false }));
      }
    },
    [
      (session?.user as any)?.id,
      session?.user?.email,
      (session?.user as any)?.firestoreUserId,
    ]
  ); // eslint-disable-line @typescript-eslint/no-explicit-any

  const contextValue: BusinessContextType = {
    // State
    businesses,
    currentBusiness,
    loadingStates,
    hasBusinesses,
    isInitialized,

    // Actions
    addBusiness,
    selectBusiness,
    refreshBusinesses,
    createAndSelectBusiness,
    getUserBusinesses,
  };

  return (
    <BusinessContext.Provider value={contextValue}>
      {children}
    </BusinessContext.Provider>
  );
}

export const useBusiness = () => {
  const context = useContext(BusinessContext);
  if (context === undefined) {
    throw new Error("useBusiness must be used within a BusinessProvider");
  }
  return context;
};
