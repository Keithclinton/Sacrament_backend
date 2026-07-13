"use server";

import { revalidatePath } from "next/cache";

import { djangoFetch } from "@/lib/djangoApi";

type Transition = "claim" | "verify" | "reject" | "suspend" | "reinstate";

export async function transitionPriestAction(priestId: number, transition: Transition, formData: FormData) {
  const notes = String(formData.get("notes") ?? "");
  await djangoFetch(`/api/clergy/priests/${priestId}/${transition}/`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
  revalidatePath("/admin/verification-queue");
}
