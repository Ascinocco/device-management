import { createClerkClient, verifyToken } from "@clerk/backend";

import { settings } from "../settings";

const clerkClient = createClerkClient({
  secretKey: settings.clerkSecretKey,
});

export type ClerkAuth = {
  clerkUserId: string;
  clerkOrgId: string;
};

export async function verifyClerkToken(token: string): Promise<ClerkAuth> {
  const payload = await verifyToken(token, {
    secretKey: settings.clerkSecretKey,
  });

  const clerkUserId = payload.sub;
  const clerkOrgId = payload.org_id as string | undefined;
  const issuer = payload.iss;

  if (!issuer) throw new Error("Missing Clerk token issuer");
  if (issuer !== settings.clerkJwtIssuer) {
    throw new Error("Invalid Clerk token issuer");
  }
  if (!clerkUserId) throw new Error("Missing Clerk user id");
  if (!clerkOrgId) throw new Error("Missing Clerk org id");

  return { clerkUserId, clerkOrgId };
}

export async function getClerkUserEmail(clerkUserId: string): Promise<string> {
  const user = await clerkClient.users.getUser(clerkUserId);
  const primaryId = user.primaryEmailAddressId;
  const primary = user.emailAddresses.find((e) => e.id === primaryId);
  const email = primary?.emailAddress ?? user.emailAddresses[0]?.emailAddress;
  if (!email) throw new Error("Clerk user email missing");
  return email;
}
