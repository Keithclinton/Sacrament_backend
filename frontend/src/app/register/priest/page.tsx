import { djangoFetch } from "@/lib/djangoApi";
import { PriestRegisterForm } from "@/components/PriestRegisterForm";

export default async function PriestRegisterPage() {
  const { data } = await djangoFetch("/api/dioceses/", { auth: false });
  const dioceses = ((data as { results?: unknown[] })?.results ?? []) as { id: number; name: string }[];

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Priest Registration</h1>
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <PriestRegisterForm dioceses={dioceses} />
      </div>
    </div>
  );
}
