'use client';

import { BusinessService, type Business } from '@/lib/firebase/services/business-service';
import { useSession } from 'next-auth/react';
import { createContext, useContext, useEffect, useState } from 'react';

type BusinessContextType = {
  currentBusiness: Business | null;
  isLoading: boolean;
};

const BusinessContext = createContext<BusinessContextType | undefined>(undefined);

export function BusinessProvider({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadBusiness = async () => {
      if (!session?.user?.id) return;

      try {
        setIsLoading(true);
        const business = await BusinessService.getBusinessByUserEmail(session?.user?.email);
        setCurrentBusiness(business);
      } catch (error) {
        console.error('Failed to load business:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadBusiness();
  }, [session?.user?.email]);

  return (
    <BusinessContext.Provider 
      value={{ 
        currentBusiness,
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