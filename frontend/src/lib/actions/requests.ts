"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import { djangoFetch } from "@/lib/djangoApi";
import type { FormState } from "@/lib/actions/auth";

export async function createRequestAction(_prevState: FormState, formData: FormData): Promise<FormState> {
  const payload: Record<string, unknown> = {
    requester_name: formData.get("requester_name"),
    requester_phone: formData.get("requester_phone"),
    patient_name: formData.get("patient_name"),
    sacrament_type: formData.get("sacrament_type"),
    emergency_level: formData.get("emergency_level"),
    location_description: formData.get("location_description"),
    hospital_or_home: formData.get("hospital_or_home"),
    family_contact_name: formData.get("family_contact_name") || "",
    family_contact_phone: formData.get("family_contact_phone") || "",
    logistics_notes: formData.get("logistics_notes") || "",
  };

  const lat = formData.get("latitude");
  const lng = formData.get("longitude");
  if (lat && lng) {
    payload.latitude = Number(lat);
    payload.longitude = Number(lng);
  }

  const { status, data } = await djangoFetch("/api/requests/", {
    method: "POST",
    body: JSON.stringify(payload),
    auth: false,
  });

  if (status !== 201) {
    return { error: firstErrorMessage(data) };
  }

  const trackingCode = (data as { tracking_code: string }).tracking_code;
  redirect(`/track/${trackingCode}?created=1`);
}

export async function acceptRequestAction(requestId: string) {
  await djangoFetch(`/api/requests/${requestId}/accept/`, { method: "POST" });
  revalidatePath("/priest/dashboard");
}

export async function declineRequestAction(requestId: string) {
  await djangoFetch(`/api/requests/${requestId}/decline/`, { method: "POST" });
  revalidatePath("/priest/dashboard");
}

export async function updateRequestStatusAction(requestId: string, status: "en_route" | "completed") {
  await djangoFetch(`/api/requests/${requestId}/status/`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
  revalidatePath("/priest/dashboard");
}

export async function toggleAvailabilityAction(currentlyAvailable: boolean) {
  await djangoFetch("/api/clergy/priests/me/", {
    method: "PATCH",
    body: JSON.stringify({ is_available: !currentlyAvailable }),
  });
  revalidatePath("/priest/dashboard");
}

export async function updatePriestLocationAction(latitude: number, longitude: number) {
  // Required for a priest to ever be matched by find_nearest_available_priests()
  // (apps/routing/services.py) - with no current_location set, they're
  // silently excluded from every routing query, forever.
  await djangoFetch("/api/clergy/priests/me/", {
    method: "PATCH",
    body: JSON.stringify({ latitude, longitude }),
  });
  revalidatePath("/priest/dashboard");
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
