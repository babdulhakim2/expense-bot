import { DecodedIdToken } from "firebase-admin/auth";
import { User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { adminAuth } from "@/lib/firebase/firebase-admin";



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

const authConfig = {
  providers: [
    CredentialsProvider({
      credentials: {
        email: { label: "Email", type: "email" },
        signInLink: { label: "Sign In Link", type: "text" },
      },
      async authorize(credentials: any): Promise<User | null> { // eslint-disable-line @typescript-eslint/no-explicit-any
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
        } catch {
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt" as const,
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }: { token: any; user?: User }) { // eslint-disable-line @typescript-eslint/no-explicit-any
      if (user) {
        token.id = user.id;
        token.email = user.email || null;
        token.idToken = user.idToken;
        token.firestoreUserId = user.firestoreUserId;
      }
      return token;
    },
    async session({ session, token }: { session: any; token: any }) { // eslint-disable-line @typescript-eslint/no-explicit-any
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

export const authOptions = authConfig as any; // eslint-disable-line @typescript-eslint/no-explicit-any
