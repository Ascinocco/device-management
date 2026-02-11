import { OrganizationSwitcher, SignedIn, SignedOut } from "@clerk/clerk-react";
import { Navigate } from "react-router-dom";

export function OrgGate() {
  return (
    <>
      <SignedIn>
        <div className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-xl font-semibold">Select organization</h2>
          <OrganizationSwitcher
            createOrganizationUrl="/orgs/new"
            hidePersonal
            afterSelectOrganizationUrl="/app"
          />
        </div>
      </SignedIn>
      <SignedOut>
        <Navigate to="/sign-in" replace />
      </SignedOut>
    </>
  );
}
