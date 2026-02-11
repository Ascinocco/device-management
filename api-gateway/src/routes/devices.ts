import { Hono } from "hono";

import { resolveIdentity } from "../auth/tenancy";
import { getClerkUserEmail, verifyClerkToken } from "../auth/clerk";
import { fetchWithTimeout } from "../fetch-with-timeout";
import { settings } from "../settings";

export const devicesRouter = new Hono();

async function proxyDevices(c: Parameters<typeof devicesRouter.all>[1]) {
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

  const url = new URL(c.req.url);
  const path = url.pathname.startsWith("/api/v1")
    ? url.pathname
    : `/api/v1${url.pathname}`;
  const upstream = `${settings.deviceServiceUrl}${path}${url.search}`;

  const res = await fetchWithTimeout(
    upstream,
    {
      method: c.req.method,
      headers: {
        "content-type": c.req.header("content-type") ?? "application/json",
        "x-user-id": userId,
        "x-tenant-id": tenantId,
        "x-internal-token": settings.deviceServiceToken,
      },
      body: c.req.method === "GET" ? undefined : await c.req.text(),
    },
    settings.proxyTimeoutMs
  );

  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/json",
    },
  });
}

devicesRouter.all("/", proxyDevices);
devicesRouter.all("/*", proxyDevices);
