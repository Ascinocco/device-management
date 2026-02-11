import {
  pgTable,
  uuid,
  varchar,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

export const tenants = pgTable(
  "tenants",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    name: varchar("name", { length: 128 }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  },
  (table) => [uniqueIndex("uq_tenant_name").on(table.name)],
);

export const users = pgTable(
  "users",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    email: varchar("email", { length: 256 }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  },
  (table) => [uniqueIndex("uq_user_email").on(table.email)],
);

export const memberships = pgTable(
  "memberships",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    tenantId: uuid("tenant_id").notNull(),
    userId: uuid("user_id").notNull(),
    role: varchar("role", { length: 64 }).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  },
  (table) => [uniqueIndex("uq_membership").on(table.tenantId, table.userId)],
);

export const authProviders = pgTable(
  "auth_providers",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    provider: varchar("provider", { length: 64 }).notNull(),
    providerUserId: varchar("provider_user_id", { length: 256 }).notNull(),
    userId: uuid("user_id").notNull(),
  },
  (table) => [
    uniqueIndex("uq_provider_user").on(table.provider, table.providerUserId),
  ],
);

export const tenantProviders = pgTable(
  "tenant_providers",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    provider: varchar("provider", { length: 64 }).notNull(),
    providerOrgId: varchar("provider_org_id", { length: 256 }).notNull(),
    tenantId: uuid("tenant_id").notNull(),
  },
  (table) => [
    uniqueIndex("uq_provider_org").on(table.provider, table.providerOrgId),
  ],
);
