import { djangoFetch } from "@/lib/djangoApi";
import { transitionPriestAction } from "@/lib/actions/clergy";

interface PriestQueueItem {
  id: number;
  diocese: number;
  diocesan_id_number: string;
  verification_status: string;
  ordination_date: string | null;
}

export default async function VerificationQueuePage() {
  const { data } = await djangoFetch("/api/clergy/verification-queue/");
  const priests = ((data as { results?: PriestQueueItem[] })?.results ?? []) as PriestQueueItem[];

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Priest Verification Queue</h1>
      <p className="text-neutral-600 mb-6 text-sm">
        Only verified priests can respond to requests. Confirm the diocesan ID number against
        your diocese&apos;s records before verifying.
      </p>
      {priests.length === 0 && <p className="text-neutral-500">Nothing pending review.</p>}
      <div className="space-y-4">
        {priests.map((p) => (
          <div key={p.id} className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Diocesan ID: {p.diocesan_id_number}</p>
                <p className="text-sm text-neutral-500">
                  Status: <span className="font-medium">{p.verification_status}</span>
                </p>
              </div>
            </div>
            <form action={transitionPriestAction.bind(null, p.id, "reject")} className="mt-3">
              <textarea
                name="notes"
                placeholder="Notes (required to reject, optional otherwise)"
                rows={2}
                className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm"
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {p.verification_status === "pending" && (
                  <ActionButton transition="claim" priestId={p.id} label="Claim for review" />
                )}
                {p.verification_status === "under_review" && (
                  <>
                    <ActionButton transition="verify" priestId={p.id} label="Verify" variant="approve" />
                    <button
                      type="submit"
                      formAction={transitionPriestAction.bind(null, p.id, "reject")}
                      className="rounded-md border border-red-300 bg-red-50 px-3 py-1.5 text-sm text-red-800 hover:bg-red-100 cursor-pointer"
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            </form>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionButton({
  transition,
  priestId,
  label,
  variant = "default",
}: {
  transition: "claim" | "verify" | "suspend" | "reinstate";
  priestId: number;
  label: string;
  variant?: "default" | "approve";
}) {
  return (
    <button
      type="submit"
      formAction={transitionPriestAction.bind(null, priestId, transition)}
      className={`rounded-md px-3 py-1.5 text-sm font-medium cursor-pointer ${
        variant === "approve"
          ? "bg-green-700 text-white hover:bg-green-800"
          : "border border-neutral-300 text-neutral-700 hover:bg-neutral-50"
      }`}
    >
      {label}
    </button>
  );
}
