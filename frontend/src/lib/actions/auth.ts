"use server";

import { redirect } from "next/navigation";

import { decodeJwt, clearSessionCookies, setSessionCookies } from "@/lib/session";

const BASE_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000";

export interface FormState {
  error: string | null;
}

function dashboardPathForRole(role: string): string {
  if (role === "priest") return "/priest/dashboard";
  if (role === "diocesan_admin" || role === "super_admin") return "/admin/verification-queue";
  return "/";
}

export async function loginAction(_prevState: FormState, formData: FormData): Promise<FormState> {
  const username = String(formData.get("username") ?? "");
  const password = String(formData.get("password") ?? "");

  const response = await fetch(`${BASE_URL}/api/accounts/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    cache: "no-store",
  });

  if (!response.ok) {
    return { error: "Invalid username or password." };
  }

  const data = (await response.json()) as { access: string; refresh: string };
  await setSessionCookies(data.access, data.refresh);

  const claims = decodeJwt(data.access);
  redirect(dashboardPathForRole(claims?.role ?? "member"));
}

export async function logoutAction() {
  await clearSessionCookies();
  redirect("/login");
}

export async function registerMemberAction(_prevState: FormState, formData: FormData): Promise<FormState> {
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch(`${BASE_URL}/api/accounts/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    return { error: firstErrorMessage(data) };
  }

  redirect("/login?registered=1");
}

export async function registerPriestAction(_prevState: FormState, formData: FormData): Promise<FormState> {
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch(`${BASE_URL}/api/clergy/priests/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    return { error: firstErrorMessage(data) };
  }

  redirect("/login?priest_registered=1");
}

function firstErrorMessage(data: unknown): string {
  if (data && typeof data === "object") {
    const values = Object.values(data as Record<string, unknown>);
    const first = values[0];
    if (Array.isArray(first)) return String(first[0]);
    if (typeof first === "string") return first;
  }
  return "Something went wrong. Please check your input and try again.";
}
