"use client";

import { useState, useTransition } from "react";

import { updatePriestLocationAction } from "@/lib/actions/requests";

export function PriestLocationButton({ hasLocation }: { hasLocation: boolean }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [justUpdated, setJustUpdated] = useState(false);

  function shareLocation() {
    if (!("geolocation" in navigator)) {
      setError("Your browser doesn't support location sharing.");
      return;
    }
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        startTransition(async () => {
          await updatePriestLocationAction(position.coords.latitude, position.coords.longitude);
          setJustUpdated(true);
        });
      },
      () => setError("Couldn't get your location. Check your browser's location permission."),
    );
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={shareLocation}
        disabled={pending}
        className={`rounded-md border px-3 py-1.5 text-sm font-medium cursor-pointer disabled:opacity-50 ${
          hasLocation
            ? "border-neutral-300 text-neutral-700 hover:bg-neutral-50"
            : "border-amber-400 bg-amber-50 text-amber-900"
        }`}
      >
        {pending
          ? "Updating…"
          : justUpdated
            ? "Location updated ✓"
            : hasLocation
              ? "Update my location"
              : "Share my location (required to receive requests)"}
      </button>
      {error && <span className="text-xs text-red-700">{error}</span>}
    </div>
  );
}
