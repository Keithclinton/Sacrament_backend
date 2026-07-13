"use client";

import { useFormStatus } from "react-dom";

export function SubmitButton({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className={`rounded-md bg-blue-900 px-4 py-2 text-white font-medium hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer ${className}`}
    >
      {pending ? "Please wait…" : children}
    </button>
  );
}
