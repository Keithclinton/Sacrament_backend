import Link from "next/link";

import { RequestForm } from "@/components/RequestForm";

export default function HomePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-blue-900">Request a Priest</h1>
        <p className="mt-2 text-neutral-600">
          For the sick, elderly, hospitalized, or dying who need urgent sacramental care. No
          account needed - just fill in the details below and we&apos;ll notify the nearest
          available verified priest.
        </p>
        <p className="mt-2 text-sm text-neutral-500">
          Already submitted a request?{" "}
          <Link href="/track" className="text-blue-900 underline">
            Track its status
          </Link>
          . Are you a priest?{" "}
          <Link href="/register/priest" className="text-blue-900 underline">
            Register here
          </Link>
          .
        </p>
      </div>
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <RequestForm />
      </div>
    </div>
  );
}
