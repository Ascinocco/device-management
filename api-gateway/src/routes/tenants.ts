import { Hono } from "hono";
import { z, ZodError } from "zod";

import { resolveIdentity } from "../auth/tenancy";
import { getClerkUserEmail, verifyClerkToken } from "../auth/clerk";
import { fetchWithTimeout } from "../fetch-with-timeout";
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

  try {
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

    const res = await fetchWithTimeout(
      `${settings.tenancyServiceUrl}/internal/tenants/${tenantId}/name`,
      {
        method: "PATCH",
        headers: {
          "content-type": "application/json",
          "x-internal-token": settings.tenancyServiceToken,
        },
        body: JSON.stringify({ userId, name: body.name }),
      },
      settings.proxyTimeoutMs
    );

    const data = await res.text();
    return new Response(data, {
      status: res.status,
      headers: {
        "content-type": res.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (err) {
    if (err instanceof ZodError) {
      return c.json({ error: "validation failed", details: err.errors }, 400);
    }
    console.error("[tenants] patch error:", err);
    return c.json({ error: "internal server error" }, 500);
  }
});
