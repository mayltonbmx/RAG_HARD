export { auth as middleware } from "@/auth";

export const config = {
  // Protect all routes except login page, API auth routes, and static assets
  matcher: [
    "/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)",
  ],
};
