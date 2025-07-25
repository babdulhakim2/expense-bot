'use client';

import { BusinessService, type Business } from '@/lib/firebase/services/business-service';
// import { UserService } from '@/lib/firebase/services/user-service';
import { useSession } from 'next-auth/react';
import { createContext, useContext, useEffect, useState, useCallback } from 'react';

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
  createAndSelectBusiness: (data: { name: string; type: string; location?: string }) => Promise<Business>;
  getUserBusinesses: () => Promise<Business[]>;
};

const BusinessContext = createContext<BusinessContextType | undefined>(undefined);

export function BusinessProvider({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(null);
  const [loadingStates, setLoadingStates] = useState<LoadingStates>({
    loading: true,
    creating: false,
    selecting: false,
  });
  const [isInitialized, setIsInitialized] = useState(false);

  // Computed values
  const hasBusinesses = businesses.length > 0;

  // Load businesses for the current user
  const loadBusinesses = useCallback(async () => {
    if (!session?.user?.email) {
      setIsInitialized(true);
      setLoadingStates(prev => ({ ...prev, loading: false }));
      return;
    }

    try {
      setLoadingStates(prev => ({ ...prev, loading: true }));
      
      // Try to get all businesses for this user
      const userBusinesses = await BusinessService.getUserBusinesses(session.user.id);
      setBusinesses(userBusinesses);
      
      // If we have businesses but no current business, select the first one
      if (userBusinesses.length > 0 && !currentBusiness) {
        setCurrentBusiness(userBusinesses[0]);
      } else if (userBusinesses.length === 0) {
        setCurrentBusiness(null);
      }
      
    } catch (error) {
      console.error('Failed to load businesses:', error);
      // Fallback: try the old method
      try {
        const business = await BusinessService.getBusinessByUserEmail(session.user.email);
        if (business) {
          setBusinesses([business]);
          setCurrentBusiness(business);
        }
      } catch (fallbackError) {
        console.error('Fallback business load also failed:', fallbackError);
        setBusinesses([]);
        setCurrentBusiness(null);
      }
    } finally {
      setLoadingStates(prev => ({ ...prev, loading: false }));
      setIsInitialized(true);
    }
  }, [session?.user?.email, session?.user?.id, currentBusiness]);

  // Initial load
  useEffect(() => {
    loadBusinesses();
  }, [loadBusinesses]);

  // Actions
  const addBusiness = useCallback((business: Business) => {
    setBusinesses(prev => [...prev, business]);
  }, []);

  const selectBusiness = useCallback(async (business: Business) => {
    try {
      setLoadingStates(prev => ({ ...prev, selecting: true }));
      setCurrentBusiness(business);
      
    } catch (error) {
      console.error('Failed to select business:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, selecting: false }));
    }
  }, []);

  const refreshBusinesses = useCallback(async () => {
    await loadBusinesses();
  }, [loadBusinesses]);

  const getUserBusinesses = useCallback(async (): Promise<Business[]> => {
    if (!session?.user?.id) return [];
    try {
      // Use the Firestore user ID (which is same as Firebase Auth UID for consistency)
      const firestoreUserId = session.user.firestoreUserId || session.user.id;
      return await BusinessService.getUserBusinesses(firestoreUserId);
    } catch (error) {
      console.error('Failed to get user businesses:', error);
      return [];
    }
  }, [session?.user?.id, session?.user?.firestoreUserId]);

  const createAndSelectBusiness = useCallback(async (data: { 
    name: string; 
    type: string; 
    location?: string 
  }): Promise<Business> => {
    if (!session?.user?.id || !session?.user?.email) {
      throw new Error('User session required');
    }

    try {
      setLoadingStates(prev => ({ ...prev, creating: true }));
      
      // Use the Firestore user ID (which is same as Firebase Auth UID for consistency)
      const firestoreUserId = session.user.firestoreUserId || session.user.id;
      
      // Create the business
      const newBusiness = await BusinessService.createBusiness({
        name: data.name,
        type: data.type,
        location: data.location || '',
        currency: 'GBP', // Default currency
        userId: firestoreUserId, // Use Firestore user ID
        primaryEmail: session.user.email,
      });

      // Add to local state
      setBusinesses(prev => [...prev, newBusiness]);
      setCurrentBusiness(newBusiness);
      
      return newBusiness;
      
    } catch (error) {
      console.error('Failed to create business:', error);
      throw error;
    } finally {
      setLoadingStates(prev => ({ ...prev, creating: false }));
    }
  }, [session?.user?.id, session?.user?.email]);

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
    throw new Error('useBusiness must be used within a BusinessProvider');
  }
  return context;
}; 