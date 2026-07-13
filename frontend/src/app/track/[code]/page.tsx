import { djangoFetch } from "@/lib/djangoApi";

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted - awaiting routing",
  routed: "Routed to a nearby priest",
  accepted: "Accepted - a priest is on the way",
  en_route: "Priest en route",
  completed: "Completed",
  cancelled: "Cancelled",
  expired: "Expired",
};

export default async function TrackResultPage({
  params,
  searchParams,
}: {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ created?: string }>;
}) {
  const { code } = await params;
  const { created } = await searchParams;

  const { status, data } = await djangoFetch(`/api/requests/track/${encodeURIComponent(code)}/`, {
    auth: false,
  });

  if (status !== 200) {
    return (
      <div className="max-w-md">
        <h1 className="text-2xl font-bold text-blue-900 mb-4">Track your request</h1>
        <p className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-800">
          No request found with reference &ldquo;{code}&rdquo;.
        </p>
      </div>
    );
  }

  const result = data as {
    tracking_code: string;
    status: string;
    sacrament_type: string;
    submitted_at: string;
  };

  return (
    <div className="max-w-md">
      {created && (
        <p className="mb-4 rounded-md bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">
          Your request has been submitted. Save this reference code.
        </p>
      )}
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Request {result.tracking_code}</h1>
      <dl className="space-y-3 rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <div>
          <dt className="text-sm text-neutral-500">Status</dt>
          <dd className="text-lg font-medium">
            {STATUS_LABELS[result.status] ?? result.status}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-neutral-500">Submitted</dt>
          <dd>{new Date(result.submitted_at).toLocaleString()}</dd>
        </div>
      </dl>
    </div>
  );
}
