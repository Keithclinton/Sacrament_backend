import { redirect } from "next/navigation";

async function goToTrackingPage(formData: FormData) {
  "use server";
  const code = String(formData.get("code") ?? "").trim().toUpperCase();
  if (code) redirect(`/track/${encodeURIComponent(code)}`);
}

export default function TrackSearchPage() {
  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Track your request</h1>
      <form action={goToTrackingPage} className="flex gap-2">
        <input
          name="code"
          placeholder="SAC-XXXXX"
          required
          className="flex-1 rounded-md border border-neutral-300 px-3 py-2"
        />
        <button
          type="submit"
          className="rounded-md bg-blue-900 px-4 py-2 text-white font-medium hover:bg-blue-800 cursor-pointer"
        >
          Track
        </button>
      </form>
    </div>
  );
}
