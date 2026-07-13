import { RegisterMemberForm } from "@/components/RegisterMemberForm";

export default function RegisterMemberPage() {
  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Create an account</h1>
      <p className="mb-4 text-sm text-neutral-600">
        An account isn&apos;t required to request a priest - but if you&apos;d like to keep a
        history of your requests, you can create one here.
      </p>
      <div className="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <RegisterMemberForm />
      </div>
    </div>
  );
}
