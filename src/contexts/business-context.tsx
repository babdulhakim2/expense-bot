'use client';

import { BusinessService, type Business } from '@/lib/firebase/services/business-service';
import { useSession } from 'next-auth/react';
import { createContext, useContext, useEffect, useState } from 'react';

type BusinessContextType = {
  currentBusiness: Business | null;
  setCurrentBusiness: (business: Business | null) => void;
  businesses: Business[];
  setBusinesses: (businesses: Business[]) => void;
  addBusiness: (business: Omit<Business, 'id' | 'createdAt' | 'updatedAt'>) => void;
  isLoading: boolean;
};

const BusinessContext = createContext<BusinessContextType | undefined>(undefined);


export function BusinessProvider({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadBusinesses = async () => {
      if (!session?.user?.id) return;

      try {
        setIsLoading(true);
        const userBusinesses = await BusinessService.getUserBusinesses(session.user.id);
        setBusinesses(userBusinesses);
        
        if (!currentBusiness && userBusinesses.length > 0) {
          setCurrentBusiness(userBusinesses[0]);
        }
      } catch (error) {
        console.error('Failed to load businesses:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadBusinesses();
  }, [session?.user?.id]);

  const addBusiness = async (businessData: Omit<Business, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      // Create new business object
      const newBusiness = {
        ...businessData,
        id: `business_${Date.now()}`,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      // Update state
      const updatedBusinesses = [...businesses, newBusiness];
      setBusinesses(updatedBusinesses);
      
      // Save to localStorage
      localStorage.setItem('businesses', JSON.stringify(updatedBusinesses));
      
      // Set as current if first business
      if (businesses.length === 0) {
        setCurrentBusiness(newBusiness);
      }

      return newBusiness;
    } catch (error) {
      console.error('Failed to add business:', error);
      throw error;
    }
  };

  return (
    <BusinessContext.Provider 
      value={{ 
        currentBusiness, 
        setCurrentBusiness, 
        businesses, 
        setBusinesses,
        addBusiness,
        isLoading 
      }}
    >
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