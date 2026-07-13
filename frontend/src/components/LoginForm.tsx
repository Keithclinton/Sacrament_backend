"use client";

import { useActionState } from "react";

import { loginAction } from "@/lib/actions/auth";
import { SubmitButton } from "@/components/SubmitButton";

const initialState = { error: null };

export function LoginForm() {
  const [state, formAction] = useActionState(loginAction, initialState);

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <p className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">
          {state.error}
        </p>
      )}
      <div>
        <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          name="username"
          required
          autoFocus
          className="w-full rounded-md border border-neutral-400 px-3 py-2 font-medium text-neutral-900 placeholder:text-neutral-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
        />
      </div>
      <div>
        <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          className="w-full rounded-md border border-neutral-400 px-3 py-2 font-medium text-neutral-900 placeholder:text-neutral-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
        />
      </div>
      <SubmitButton className="w-full">Log in</SubmitButton>
    </form>
  );
}
