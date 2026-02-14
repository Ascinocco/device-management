import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";

import { devicesRouter } from "./routes/devices";
import { tenantsRouter } from "./routes/tenants";
import { settings } from "./settings";

const app = new Hono();

app.use(
  "*", // this should be restricted to allowed domains
  cors({
    origin: settings.corsOrigins,
    allowHeaders: ["Authorization", "Content-Type"],
    allowMethods: ["GET", "POST", "PATCH", "OPTIONS"],
  })
);

app.onError((err, c) => {
  console.error("[gateway] unhandled error:", err);
  return c.json({ error: "internal server error" }, 500);
});

app.route("/api/v1/devices", devicesRouter);
app.route("/api/v1/tenants", tenantsRouter);

app.get("/health", (c) => c.json({ ok: true }));

console.log(`API gateway listening on http://localhost:${settings.port}`);
serve({ fetch: app.fetch, port: settings.port });
