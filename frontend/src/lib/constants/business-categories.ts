export const BUSINESS_CATEGORIES = [
  { id: 'technology', label: 'Technology', icon: '💻' },
  { id: 'retail', label: 'Retail', icon: '🏪' },
  { id: 'finance', label: 'Finance', icon: '💰' },
  { id: 'healthcare', label: 'Healthcare', icon: '🏥' },
  { id: 'education', label: 'Education', icon: '📚' },
  { id: 'food', label: 'Food & Beverage', icon: '🍽️' },
  { id: 'real_estate', label: 'Real Estate', icon: '🏢' },
  { id: 'manufacturing', label: 'Manufacturing', icon: '🏭' },
  { id: 'consulting', label: 'Consulting', icon: '💼' },
  { id: 'other', label: 'Other', icon: '🔧' }
] as const;

export type BusinessCategory = typeof BUSINESS_CATEGORIES[number]['id']; 