"use client";

import { useActionState } from "react";

import { registerMemberAction } from "@/lib/actions/auth";
import { SubmitButton } from "@/components/SubmitButton";

const initialState = { error: null };

export function RegisterMemberForm() {
  const [state, formAction] = useActionState(registerMemberAction, initialState);

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <p className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">
          {state.error}
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="First name" name="first_name" required />
        <TextField label="Last name" name="last_name" required />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="Username" name="username" required />
        <TextField label="Email" name="email" type="email" />
      </div>
      <TextField label="Phone number" name="phone_number" type="tel" required />
      <TextField label="Password" name="password" type="password" required />
      <SubmitButton className="w-full">Create account</SubmitButton>
    </form>
  );
}

function TextField({
  label,
  name,
  type = "text",
  required = false,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor={name}>
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        className="w-full rounded-md border border-neutral-400 px-3 py-2 font-medium text-neutral-900 placeholder:text-neutral-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
      />
    </div>
  );
}
