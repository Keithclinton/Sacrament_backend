import Link from "next/link";

import { LoginForm } from "@/components/LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ registered?: string; priest_registered?: string }>;
}) {
  const { registered, priest_registered } = await searchParams;

  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Priest / Admin Login</h1>
      {registered && (
        <p className="mb-4 rounded-md bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">
          Account created. Log in below.
        </p>
      )}
      {priest_registered && (
        <p className="mb-4 rounded-md bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">
          Registration received. Your diocese will review it before you get dashboard access.
        </p>
      )}
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <LoginForm />
      </div>
      <p className="mt-4 text-sm text-neutral-600">
        No account?{" "}
        <Link href="/register/priest" className="text-blue-900 underline">
          Register as a priest
        </Link>
        .
      </p>
    </div>
  );
}
