declare module "next-auth" {
  interface User {
    id: string;
    name?: string | null;
    phoneNumber?: string | null;
    idToken?: string;
    email?: string | null;
    firestoreUserId?: string;
  }


  interface Session {
    user: User & {
      id: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    email?: string | null;
    phoneNumber?: string;
    idToken?: string;
    firestoreUserId?: string;
  }
}
