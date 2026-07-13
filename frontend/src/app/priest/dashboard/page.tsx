import { djangoFetch } from "@/lib/djangoApi";
import {
  acceptRequestAction,
  declineRequestAction,
  toggleAvailabilityAction,
  updateRequestStatusAction,
} from "@/lib/actions/requests";
import { PriestLocationButton } from "@/components/PriestLocationButton";

interface SacramentRequestItem {
  id: string;
  tracking_code: string;
  patient_name: string;
  sacrament_type: string;
  emergency_level: string;
  location_description: string;
  status: string;
  assigned_priest: number | null;
  logistics_notes: string;
}

const EMERGENCY_STYLES: Record<string, string> = {
  emergency_danger_of_death: "bg-red-100 text-red-800 border-red-300",
  urgent: "bg-amber-100 text-amber-800 border-amber-300",
  routine: "bg-neutral-100 text-neutral-700 border-neutral-300",
};

export default async function PriestDashboardPage() {
  const { data: profileData } = await djangoFetch("/api/clergy/priests/me/");
  const profile = profileData as {
    is_available: boolean;
    verification_status: string;
    has_location: boolean;
  };

  if (profile.verification_status !== "verified") {
    return (
      <div className="max-w-md rounded-lg border border-amber-200 bg-amber-50 p-6">
        <h1 className="text-xl font-bold text-amber-900 mb-2">Registration under review</h1>
        <p className="text-sm text-amber-800">
          Your diocese hasn&apos;t verified your registration yet
          (status: <span className="font-medium">{profile.verification_status.replace(/_/g, " ")}</span>).
          You&apos;ll be notified by SMS/email once that&apos;s done - dashboard access unlocks
          automatically after verification.
        </p>
      </div>
    );
  }

  const { data: requestsData } = await djangoFetch("/api/requests/mine/");
  const requests = ((requestsData as { results?: SacramentRequestItem[] })?.results ??
    []) as SacramentRequestItem[];

  const pending = requests.filter((r) => r.status === "routed" && !r.assigned_priest);
  const active = requests.filter((r) => ["accepted", "en_route"].includes(r.status));

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-blue-900">My Dashboard</h1>
        <div className="flex items-center gap-3">
          <PriestLocationButton hasLocation={profile.has_location} />
          <form action={toggleAvailabilityAction.bind(null, profile.is_available)}>
            <button
              type="submit"
              className={`rounded-md border px-3 py-1.5 text-sm font-medium cursor-pointer ${
                profile.is_available
                  ? "border-green-300 bg-green-50 text-green-800"
                  : "border-neutral-300 bg-neutral-100 text-neutral-600"
              }`}
            >
              {profile.is_available ? "Available - tap to go offline" : "Offline - tap to go available"}
            </button>
          </form>
        </div>
      </div>

      {!profile.has_location && (
        <p className="rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-900">
          You haven&apos;t shared your location yet - you won&apos;t be matched to any requests until
          you do.
        </p>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-3">Awaiting your response ({pending.length})</h2>
        {pending.length === 0 && <p className="text-neutral-500 text-sm">Nothing right now.</p>}
        <div className="space-y-3">
          {pending.map((r) => (
            <div key={r.id} className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
              <RequestSummary r={r} />
              <div className="mt-3 flex gap-2">
                <form action={acceptRequestAction.bind(null, r.id)}>
                  <button
                    type="submit"
                    className="rounded-md bg-green-700 px-3 py-1.5 text-sm text-white font-medium hover:bg-green-800 cursor-pointer"
                  >
                    Accept
                  </button>
                </form>
                <form action={declineRequestAction.bind(null, r.id)}>
                  <button
                    type="submit"
                    className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-50 cursor-pointer"
                  >
                    Decline
                  </button>
                </form>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Your active requests ({active.length})</h2>
        {active.length === 0 && <p className="text-neutral-500 text-sm">None right now.</p>}
        <div className="space-y-3">
          {active.map((r) => (
            <div key={r.id} className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
              <RequestSummary r={r} />
              <div className="mt-3 flex gap-2">
                {r.status === "accepted" && (
                  <form action={updateRequestStatusAction.bind(null, r.id, "en_route")}>
                    <button
                      type="submit"
                      className="rounded-md bg-blue-900 px-3 py-1.5 text-sm text-white font-medium hover:bg-blue-800 cursor-pointer"
                    >
                      Mark en route
                    </button>
                  </form>
                )}
                <form action={updateRequestStatusAction.bind(null, r.id, "completed")}>
                  <button
                    type="submit"
                    className="rounded-md border border-green-700 px-3 py-1.5 text-sm text-green-800 hover:bg-green-50 cursor-pointer"
                  >
                    Mark completed
                  </button>
                </form>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function RequestSummary({ r }: { r: SacramentRequestItem }) {
  return (
    <div>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono text-xs text-neutral-500">{r.tracking_code}</span>
        <span
          className={`text-xs px-2 py-0.5 rounded-full border ${EMERGENCY_STYLES[r.emergency_level] ?? ""}`}
        >
          {r.emergency_level.replace(/_/g, " ")}
        </span>
      </div>
      <p className="font-medium mt-1">
        {r.sacrament_type.replace(/_/g, " ")} for {r.patient_name}
      </p>
      <p className="text-sm text-neutral-600">{r.location_description}</p>
      {r.logistics_notes && (
        <p className="text-sm text-neutral-500 mt-1">Notes: {r.logistics_notes}</p>
      )}
    </div>
  );
}
