import { Hono } from "hono";
import { z } from "zod";

import { resolveIdentity } from "../auth/tenancy";
import { getClerkUserEmail, verifyClerkToken } from "../auth/clerk";
import { settings } from "../settings";

const updateSchema = z.object({
  name: z.string().min(1),
});

export const tenantsRouter = new Hono();

tenantsRouter.patch(":tenantId", async (c) => {
  const auth = c.req.header("authorization");
  if (!auth?.startsWith("Bearer ")) {
    return c.json({ error: "unauthorized" }, 401);
  }
  const token = auth.slice("Bearer ".length);

  const { clerkUserId, clerkOrgId } = await verifyClerkToken(token);
  const email = await getClerkUserEmail(clerkUserId);
  const { userId, tenantId } = await resolveIdentity(
    clerkUserId,
    clerkOrgId,
    email
  );

  if (tenantId !== c.req.param("tenantId")) {
    return c.json({ error: "forbidden" }, 403);
  }

  const body = updateSchema.parse(await c.req.json());

  const res = await fetch(
    `${settings.tenancyServiceUrl}/internal/tenants/${tenantId}/name`,
    {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        "x-internal-token": settings.tenancyServiceToken,
      },
      body: JSON.stringify({ userId, name: body.name }),
    }
  );

  const data = await res.text();
  return new Response(data, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
    },
  });
});
