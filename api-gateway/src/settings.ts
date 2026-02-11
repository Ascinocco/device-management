import dotenv from "dotenv";
dotenv.config();

type EnvKey =
  | "PORT"
  | "CLERK_SECRET_KEY"
  | "CLERK_JWT_ISSUER"
  | "TENANCY_SERVICE_URL"
  | "TENANCY_SERVICE_TOKEN"
  | "DEVICE_SERVICE_URL"
  | "DEVICE_SERVICE_TOKEN"
  | "PROXY_TIMEOUT_MS";

function requireEnv(key: EnvKey): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var: ${key}`);
  return value;
}

function optionalEnv(key: EnvKey, fallback: string): string {
  return process.env[key] ?? fallback;
}

export const settings = {
  port: Number(requireEnv("PORT")),
  clerkSecretKey: requireEnv("CLERK_SECRET_KEY"),
  clerkJwtIssuer: requireEnv("CLERK_JWT_ISSUER"),
  tenancyServiceUrl: requireEnv("TENANCY_SERVICE_URL"),
  tenancyServiceToken: requireEnv("TENANCY_SERVICE_TOKEN"),
  deviceServiceUrl: requireEnv("DEVICE_SERVICE_URL"),
  deviceServiceToken: requireEnv("DEVICE_SERVICE_TOKEN"),
  proxyTimeoutMs: Number(optionalEnv("PROXY_TIMEOUT_MS", "10000")),
};
