import { CreateOrganization, SignedIn, SignedOut } from "@clerk/clerk-react";
import { Navigate } from "react-router-dom";

export function CreateOrgPage() {
  return (
    <>
      <SignedIn>
        <div className="mx-auto flex max-w-xl flex-col gap-4 p-6">
          <h2 className="text-xl font-semibold">Create organization</h2>
          <CreateOrganization afterCreateOrganizationUrl="/app" />
        </div>
      </SignedIn>
      <SignedOut>
        <Navigate to="/sign-in" replace />
      </SignedOut>
    </>
  );
}
