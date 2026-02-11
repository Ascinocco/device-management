import { Navigate, Route, Routes } from "react-router-dom";
import {
  SignedIn,
  SignedOut,
  SignIn,
  SignUp,
  UserButton,
  useOrganization,
} from "@clerk/clerk-react";

import { LandingPage } from "./pages/LandingPage";
import { DevicesPage } from "./pages/DevicesPage";
import { DeviceDetailPage } from "./pages/DeviceDetailPage";
import { NewDevicePage } from "./pages/NewDevicePage";
import { OrgGate } from "./pages/OrgGate";
import { CreateOrgPage } from "./pages/CreateOrgPage";

function RequireOrg({ children }: { children: React.ReactNode }) {
  const { organization } = useOrganization();
  if (!organization) {
    return <Navigate to="/orgs" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <>
      <header className="flex border-b w-full">
        <div className="flex items-center justify-between py-4 px-5.5 w-full">
          <span className="font-semibold">Device Service</span>
          <UserButton />
        </div>
      </header>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/sign-in/*"
          element={<SignIn routing="path" path="/sign-in" />}
        />
        <Route
          path="/sign-up/*"
          element={<SignUp routing="path" path="/sign-up" />}
        />

        <Route path="/orgs" element={<OrgGate />} />
        <Route path="/orgs/new" element={<CreateOrgPage />} />
        <Route
          path="/app"
          element={
            <>
              <SignedIn>
                <RequireOrg>
                  <DevicesPage />
                </RequireOrg>
              </SignedIn>
              <SignedOut>
                <Navigate to="/sign-in" replace />
              </SignedOut>
            </>
          }
        />
        <Route
          path="/devices/new"
          element={
            <>
              <SignedIn>
                <RequireOrg>
                  <NewDevicePage />
                </RequireOrg>
              </SignedIn>
              <SignedOut>
                <Navigate to="/sign-in" replace />
              </SignedOut>
            </>
          }
        />
        <Route
          path="/devices/:deviceId"
          element={
            <>
              <SignedIn>
                <RequireOrg>
                  <DeviceDetailPage />
                </RequireOrg>
              </SignedIn>
              <SignedOut>
                <Navigate to="/sign-in" replace />
              </SignedOut>
            </>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
