import { djangoFetch } from "@/lib/djangoApi";

interface Summary {
  total: number;
  by_status: Record<string, number>;
  by_emergency_level: Record<string, number>;
}

export default async function AnalyticsPage() {
  const { data } = await djangoFetch("/api/requests/analytics/summary/");
  const summary = data as Summary;

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Request Analytics</h1>
      <div className="grid gap-6 sm:grid-cols-3">
        <StatCard label="Total requests" value={summary.total} />
        <BreakdownCard title="By status" counts={summary.by_status} />
        <BreakdownCard title="By emergency level" counts={summary.by_emergency_level} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-neutral-500">{label}</p>
      <p className="text-3xl font-bold text-blue-900 mt-1">{value}</p>
    </div>
  );
}

function BreakdownCard({ title, counts }: { title: string; counts: Record<string, number> }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-neutral-500 mb-2">{title}</p>
      <dl className="space-y-1">
        {Object.entries(counts).map(([key, count]) => (
          <div key={key} className="flex justify-between text-sm">
            <dt className="capitalize">{key.replace(/_/g, " ")}</dt>
            <dd className="font-medium">{count}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
