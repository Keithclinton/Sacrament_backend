"use client";

import { useActionState, useState } from "react";

import { createRequestAction } from "@/lib/actions/requests";
import { SubmitButton } from "@/components/SubmitButton";

const initialState = { error: null };

export function RequestForm() {
  const [state, formAction] = useActionState(createRequestAction, initialState);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  function useMyLocation() {
    if (!("geolocation" in navigator)) {
      setLocationError("Your browser doesn't support location sharing.");
      return;
    }
    setLocating(true);
    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lng: position.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocationError("Couldn't get your location. You can still describe it below.");
        setLocating(false);
      },
    );
  }

  return (
    <form action={formAction} className="space-y-5">
      {state.error && (
        <p className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">
          {state.error}
        </p>
      )}

      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-blue-900">Who needs help?</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Your name" name="requester_name" required />
          <Field label="Your phone number" name="requester_phone" type="tel" required />
        </div>
        <Field label="Patient's name" name="patient_name" required />
      </fieldset>

      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-blue-900">What&apos;s needed</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Sacrament needed"
            name="sacrament_type"
            required
            options={[
              ["confession", "Confession"],
              ["communion_for_sick", "Holy Communion for the Sick"],
              ["anointing_of_the_sick", "Anointing of the Sick"],
              ["last_rites", "Last Rites"],
              ["spiritual_counselling", "Spiritual Counselling"],
            ]}
          />
          <Select
            label="How urgent?"
            name="emergency_level"
            required
            options={[
              ["emergency_danger_of_death", "Emergency - danger of death"],
              ["urgent", "Urgent"],
              ["routine", "Routine"],
            ]}
          />
        </div>
      </fieldset>

      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-blue-900">Where</legend>
        <Select
          label="Location type"
          name="hospital_or_home"
          required
          options={[
            ["hospital", "Hospital"],
            ["home", "Home"],
            ["care_facility", "Care Facility"],
            ["other", "Other"],
          ]}
        />
        <div>
          <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor="location_description">
            Location / landmark (hospital name, ward, nearest town, etc.)
          </label>
          <textarea
            id="location_description"
            name="location_description"
            required
            rows={2}
            className="w-full rounded-md border border-neutral-400 px-3 py-2 font-medium text-neutral-900 placeholder:text-neutral-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={useMyLocation}
            disabled={locating}
            className="rounded-md border border-blue-900 px-3 py-1.5 text-sm text-blue-900 hover:bg-blue-50 disabled:opacity-50 cursor-pointer"
          >
            {locating ? "Locating…" : coords ? "Location shared ✓" : "Share my exact location"}
          </button>
          {locationError && <span className="text-xs text-red-700">{locationError}</span>}
        </div>
        {coords && (
          <>
            <input type="hidden" name="latitude" value={coords.lat} />
            <input type="hidden" name="longitude" value={coords.lng} />
          </>
        )}
      </fieldset>

      <fieldset className="space-y-4">
        <legend className="text-lg font-semibold text-blue-900">Optional</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Family contact name" name="family_contact_name" />
          <Field label="Family contact phone" name="family_contact_phone" type="tel" />
        </div>
        <div>
          <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor="logistics_notes">
            Logistics notes (e.g. gate code, ward number) - not for confession or spiritual content
          </label>
          <textarea
            id="logistics_notes"
            name="logistics_notes"
            rows={2}
            maxLength={1000}
            className="w-full rounded-md border border-neutral-400 px-3 py-2 font-medium text-neutral-900 placeholder:text-neutral-400 placeholder:font-normal focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
          />
        </div>
      </fieldset>

      <SubmitButton>Submit request</SubmitButton>
    </form>
  );
}

function Field({
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

function Select({
  label,
  name,
  options,
  required = false,
}: {
  label: string;
  name: string;
  options: [string, string][];
  required?: boolean;
}) {
  return (
    <div>
      <label className="block text-sm font-bold text-neutral-900 mb-1" htmlFor={name}>
        {label}
      </label>
      <select
        id={name}
        name={name}
        required={required}
        defaultValue=""
        className="w-full rounded-md border border-neutral-400 px-3 py-2 bg-white font-bold text-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-blue-900"
      >
        <option value="" disabled className="font-normal text-neutral-400">
          Select…
        </option>
        {options.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </div>
  );
}
