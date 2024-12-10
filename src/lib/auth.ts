import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { adminAuth } from "./firebase/firebase-admin";
import { User } from 'next-auth';
import { DecodedIdToken } from 'firebase-admin/auth';

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      phoneNumber?: string | null;
      idToken?: string;
    }
  }
  
  interface User {
    id: string;
    phoneNumber?: string | null;
    idToken?: string;
  }
}

interface Token {
  id?: string;
  phoneNumber?: string | null;
  idToken?: string;
}

const verifyToken = async (token: string): Promise<DecodedIdToken | null> => {
  if (process.env.NODE_ENV === 'development') {
    // In development, parse the token directly since it's from the emulator
    try {
      const [header, payload, signature] = token.split('.');
      const decodedPayload = JSON.parse(Buffer.from(payload, 'base64').toString());
      console.log('Development token payload:', decodedPayload);
      return decodedPayload;
    } catch (error) {
      console.error('Error parsing development token:', error);
      return null;
    }
  } else {
    // In production, verify the token properly
    try {
      return await adminAuth.verifyIdToken(token);
    } catch (error) {
      console.error('Error verifying production token:', error);
      return null;
    }
  }

  
};

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      credentials: {},
      async authorize(credentials: any): Promise<User | null> {
        if (!credentials?.token) {
          console.error("No token provided");
          return null;
        }

        try {
          const decodedToken = await verifyToken(credentials.token);
          if (!decodedToken) {
            console.error("Token verification failed");
            return null;
          }
          
          console.log("Token verified successfully:", decodedToken);
          
          return {
            id: decodedToken.user_id,
            phoneNumber: decodedToken.phone_number || null,
            idToken: credentials.token,
          };
          
        } catch (error) {
          console.error("Authorization error:", error);
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.phoneNumber = user.phoneNumber || undefined;
        token.idToken = user.idToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (session?.user) {
        session.user.id = token.id as string;
        session.user.phoneNumber = token.phoneNumber as string | null;
        session.user.idToken = token.idToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/',
    error: '/auth/error',
  },
  debug: process.env.NODE_ENV === 'development',
}; 