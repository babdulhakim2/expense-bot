import NextAuth from "next-auth/next";
import { authOptions } from "./authOptions";

const handler = NextAuth(authOptions); // eslint-disable-line @typescript-eslint/no-explicit-any
export { handler as GET, handler as POST };