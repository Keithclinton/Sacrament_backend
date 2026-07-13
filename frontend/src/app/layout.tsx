import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";

import { getSession } from "@/lib/session";
import { logoutAction } from "@/lib/actions/auth";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sacrament Assistance Platform",
  description: "Connecting the faithful with verified priests for urgent pastoral care.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getSession();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-neutral-50 text-neutral-900">
        <header className="border-b border-neutral-200 bg-white">
          <nav className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
            <Link href="/" className="font-semibold text-lg text-blue-900">
              Sacrament Assistance
            </Link>
            <div className="flex items-center gap-4 text-sm">
              {!session && (
                <>
                  <Link href="/track" className="hover:underline">
                    Track a request
                  </Link>
                  <Link href="/login" className="hover:underline">
                    Priest / Admin login
                  </Link>
                </>
              )}
              {session?.role === "priest" && (
                <Link href="/priest/dashboard" className="hover:underline">
                  My dashboard
                </Link>
              )}
              {(session?.role === "diocesan_admin" || session?.role === "super_admin") && (
                <>
                  <Link href="/admin/verification-queue" className="hover:underline">
                    Verification queue
                  </Link>
                  <Link href="/admin/analytics" className="hover:underline">
                    Analytics
                  </Link>
                </>
              )}
              {session && (
                <form action={logoutAction}>
                  <button type="submit" className="text-red-700 hover:underline cursor-pointer">
                    Log out
                  </button>
                </form>
              )}
            </div>
          </nav>
        </header>
        <main className="flex-1 mx-auto w-full max-w-4xl px-4 py-8">{children}</main>
        <footer className="border-t border-neutral-200 py-4 text-center text-xs text-neutral-500">
          This platform coordinates requests for physical pastoral care. It never records
          confession or any sacramental content.
        </footer>
      </body>
    </html>
  );
}
