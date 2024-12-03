export interface UserProfile {
  id: string;
  email: string;
  name: string;
  phoneNumber?: string;
  createdAt: Date;
  updatedAt: Date;
} 