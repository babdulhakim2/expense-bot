import { Business } from '@/lib/firebase/services/business-service';

const BUSINESSES_KEY = 'user_businesses';
const SELECTED_BUSINESS_KEY = 'selectedBusinessId';

export class LocalBusinessStorage {
  static getBusinesses(userEmail: string): Business[] {
    try {
      const stored = localStorage.getItem(`${BUSINESSES_KEY}_${userEmail}`);
      if (!stored) return [];
      return JSON.parse(stored);
    } catch (error) {
      console.error('Error loading businesses from localStorage:', error);
      return [];
    }
  }

  static saveBusiness(userEmail: string, business: Business): void {
    try {
      const businesses = this.getBusinesses(userEmail);
      const existingIndex = businesses.findIndex(b => b.id === business.id);
      
      if (existingIndex >= 0) {
        businesses[existingIndex] = business;
      } else {
        businesses.push(business);
      }
      
      localStorage.setItem(`${BUSINESSES_KEY}_${userEmail}`, JSON.stringify(businesses));
    } catch (error) {
      console.error('Error saving business to localStorage:', error);
    }
  }

  static getSelectedBusinessId(): string | null {
    return localStorage.getItem(SELECTED_BUSINESS_KEY);
  }

  static setSelectedBusinessId(businessId: string): void {
    localStorage.setItem(SELECTED_BUSINESS_KEY, businessId);
  }

  static getSelectedBusiness(userEmail: string): Business | null {
    const selectedId = this.getSelectedBusinessId();
    if (!selectedId) return null;
    
    const businesses = this.getBusinesses(userEmail);
    return businesses.find(b => b.id === selectedId) || null;
  }

  static clearAll(userEmail: string): void {
    localStorage.removeItem(`${BUSINESSES_KEY}_${userEmail}`);
    localStorage.removeItem(SELECTED_BUSINESS_KEY);
  }
}