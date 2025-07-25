import { DecodedIdToken } from "firebase-admin/auth";
import { NextAuthOptions, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { adminAuth } from "../../../../lib/firebase/firebase-admin";

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      name?: string | null;
      phoneNumber?: string | null;
      idToken?: string;
      email?: string | null;
      firestoreUserId?: string;
    };
  }

  interface User {
    id: string;
    phoneNumber?: string | null;
    idToken?: string;
    firestoreUserId?: string;
  }
}

const verifyToken = async (token: string): Promise<DecodedIdToken | null> => {
  if (process.env.NODE_ENV === "development") {
    // In development, parse the token directly since it's from the emulator
    try {
      const [, payload] = token.split("."); // Get the payload (second part)
      const decodedPayload = JSON.parse(
        Buffer.from(payload, "base64").toString()
      );
      console.log("Decoded token payload in development:", decodedPayload);
      return decodedPayload;
    } catch (error) {
      console.error("Error parsing development token:", error);
      return null;
    }
  } else {
    try {
      return await adminAuth.verifyIdToken(token);
    } catch (error) {
      console.error("Error verifying production token:", error);
      return null;
    }
  }
};

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      credentials: {
        email: { label: "Email", type: "email" },
        signInLink: { label: "Sign In Link", type: "text" },
      },
      async authorize(credentials: any): Promise<User | null> {
        if (!credentials?.token) {
          return null;
        }

        try {
          const decodedToken = await verifyToken(credentials.token);
          if (!decodedToken) {
            return null;
          }

          return {
            id: decodedToken.user_id,
            email: decodedToken.email || null,
            idToken: credentials.token,
            firestoreUserId: decodedToken.user_id,
          };
        } catch (error) {
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
        token.email = user.email || null;
        token.idToken = user.idToken;
        token.firestoreUserId = user.firestoreUserId;
      }
      return token;
    },
    async session({ session, token }) {
      if (session?.user) {
        session.user.id = token.id as string;
        session.user.email = token.email as string | null;
        session.user.idToken = token.idToken as string;
        session.user.firestoreUserId = token.firestoreUserId as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/",
    error: "/auth/error",
  },
  debug: process.env.NODE_ENV === "development",
};
