import NextAuth from 'next-auth';

declare module 'next-auth' {
  interface User {
    id: string;
    name?: string | null;
    phoneNumber?: string | null;
    idToken?: string;
  }
  
  interface Session {
    user: User & {
      id: string;
    };
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    phoneNumber?: string;
    idToken?: string;
  }
}