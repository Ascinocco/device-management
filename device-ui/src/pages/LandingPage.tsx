import { SignedIn, SignedOut } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="mx-auto max-w-4xl p-8">
      <h1 className="text-3xl font-semibold">Device Management</h1>
      <p className="mt-2 text-gray-600">
        Manage devices across tenants with audit-safe workflows.
      </p>

      <SignedOut>
        <div className="mt-6 flex gap-3">
          <Link className="rounded bg-black px-4 py-2 text-white" to="/sign-in">
            Sign in
          </Link>
          <Link className="rounded border px-4 py-2" to="/sign-up">
            Create account
          </Link>
        </div>
      </SignedOut>

      <SignedIn>
        <Link
          className="mt-6 inline-block rounded bg-black px-4 py-2 text-white"
          to="/app"
        >
          Go to dashboard
        </Link>
      </SignedIn>
    </div>
  );
}
