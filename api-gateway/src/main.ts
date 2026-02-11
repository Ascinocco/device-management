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
    origin: ["http://localhost:5173"],
    allowHeaders: ["Authorization", "Content-Type"],
    allowMethods: ["GET", "POST", "PATCH", "OPTIONS"],
  })
);

app.route("/api/v1/devices", devicesRouter);
app.route("/api/v1/tenants", tenantsRouter);

app.get("/health", (c) => c.json({ ok: true }));

console.log(`API gateway listening on http://localhost:${settings.port}`);
serve({ fetch: app.fetch, port: settings.port });
