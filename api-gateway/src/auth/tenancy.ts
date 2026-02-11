import { z } from "zod";

import { settings } from "../settings";

const resolveSchema = z.object({
  userId: z.string(),
  tenantId: z.string(),
});

export type ResolvedIdentity = {
  userId: string;
  tenantId: string;
};

export async function resolveIdentity(
  clerkUserId: string,
  clerkOrgId: string,
  email: string
): Promise<ResolvedIdentity> {
  const res = await fetch(`${settings.tenancyServiceUrl}/internal/resolve`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-internal-token": settings.tenancyServiceToken,
    },
    body: JSON.stringify({ clerkUserId, clerkOrgId, email }),
  });

  if (!res.ok) {
    throw new Error(`Tenancy service error: ${res.status}`);
  }

  const data = resolveSchema.parse(await res.json());
  return { userId: data.userId, tenantId: data.tenantId };
}
