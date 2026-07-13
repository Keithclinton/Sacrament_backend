"use client";

import { useActionState } from "react";

import { registerPriestAction } from "@/lib/actions/auth";
import { SubmitButton } from "@/components/SubmitButton";

const initialState = { error: null };

interface Diocese {
  id: number;
  name: string;
}

export function PriestRegisterForm({ dioceses }: { dioceses: Diocese[] }) {
  const [state, formAction] = useActionState(registerPriestAction, initialState);

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

      <div>
        <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor="diocese">
          Diocese
        </label>
        <select
          id="diocese"
          name="diocese"
          required
          defaultValue=""
          className="w-full rounded-md border border-neutral-400 px-3 py-2 bg-white font-bold text-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
        >
          <option value="" disabled className="font-normal text-neutral-400">
            Select your diocese…
          </option>
          {dioceses.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <TextField label="Diocesan ID number" name="diocesan_id_number" required />

      <p className="text-xs text-neutral-500">
        Your registration will be reviewed by your diocese before you get dashboard access. This
        is not optional - it&apos;s how the platform ensures only verified clergy can respond to
        requests.
      </p>

      <SubmitButton className="w-full">Register</SubmitButton>
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
