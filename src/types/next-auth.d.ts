import 'next-auth';

declare module 'next-auth' {
  interface User {
    phoneNumber?: string;
    id: string;
  }

  interface Session {
    user: User;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    phoneNumber?: string;
  }
}