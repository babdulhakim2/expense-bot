import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    console.log('Middleware executing for path:', req.nextUrl.pathname);
    console.log('Token exists:', !!req.nextauth.token);
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        console.log('Authorization check, token exists:', !!token);
        return !!token;
      },
    },
    pages: {
      signIn: "/",
    },
  }
);

export const config = {
  matcher: [
    '/dashboard/',
  ],
}; 