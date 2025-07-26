import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// For NextAuth v4, we need to use a different approach
// Since getToken might not be available, we'll check the session cookie
export async function middleware(request: NextRequest) {
  const sessionCookie = request.cookies.get('next-auth.session-token') || 
                       request.cookies.get('__Secure-next-auth.session-token');

  if (!sessionCookie) {
    return NextResponse.redirect(new URL('/auth/signin', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/api/business/:path*',
    '/api/banking/:path*',
  ],
}; 