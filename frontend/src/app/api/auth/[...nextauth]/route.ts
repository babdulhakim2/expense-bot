import NextAuth from "next-auth/next";
import { authOptions } from "@/app/api/auth/[...nextauth]/authOptions";

const handler = NextAuth(authOptions as any); // eslint-disable-line @typescript-eslint/no-explicit-any
export { handler as GET, handler as POST };