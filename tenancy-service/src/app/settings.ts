import dotenv from "dotenv";
dotenv.config();
type EnvKey = "DATABASE_URL" | "TENANCY_SERVICE_TOKEN" | "PORT";

function requireEnv(key: EnvKey): string {
  const value = process.env[key];
  if (!value) throw new Error(`Missing env var: ${key}`);
  return value;
}

export const settings = {
  databaseUrl: requireEnv("DATABASE_URL"),
  tenancyServiceToken: requireEnv("TENANCY_SERVICE_TOKEN"),
  port: Number(requireEnv("PORT")),
};
