import { and, eq } from "drizzle-orm";

import { IdentityRepository } from "../../app/identity/repository";
import { ResolvedIdentity } from "../../app/identity/dto";
import { db } from "../db/drizzle";
import {
  authProviders,
  memberships,
  tenantProviders,
  tenants,
  users,
} from "../db/schema";

const AUTH_PROVIDER = "clerk" as const;

export class DrizzleIdentityRepository implements IdentityRepository {
  async resolveIdentity(
    clerkUserId: string,
    clerkOrgId: string,
    email: string,
  ): Promise<ResolvedIdentity> {
    return db.transaction(async (tx) => {
      let tenantId: string | undefined;
      let userId: string | undefined;
      let isNewTenant = false;

      const tenantRow = await tx
        .select()
        .from(tenantProviders)
        .where(
          and(
            eq(tenantProviders.provider, AUTH_PROVIDER),
            eq(tenantProviders.providerOrgId, clerkOrgId),
          ),
        )
        .limit(1);

      if (tenantRow[0]) {
        tenantId = tenantRow[0].tenantId;
      } else {
        const created = await tx
          .insert(tenants)
          .values({
            name: `tenant-${clerkOrgId}`,
            createdAt: new Date(),
          })
          .returning();
        if (!created[0]) {
          throw new Error("Failed to insert tenant");
        }
        tenantId = created[0].id;
        await tx.insert(tenantProviders).values({
          provider: AUTH_PROVIDER,
          providerOrgId: clerkOrgId,
          tenantId,
        });
        isNewTenant = true;
      }

      const userRow = await tx
        .select()
        .from(authProviders)
        .where(
          and(
            eq(authProviders.provider, AUTH_PROVIDER),
            eq(authProviders.providerUserId, clerkUserId),
          ),
        )
        .limit(1);

      if (userRow[0]) {
        userId = userRow[0].userId;
        await tx.update(users).set({ email }).where(eq(users.id, userId));
      } else {
        const created = await tx
          .insert(users)
          .values({
            email,
            createdAt: new Date(),
          })
          .returning();
        if (!created[0]) {
          throw new Error("Failed to insert user");
        }
        userId = created[0].id;
        await tx.insert(authProviders).values({
          provider: AUTH_PROVIDER,
          providerUserId: clerkUserId,
          userId,
        });
      }

      await tx
        .insert(memberships)
        .values({
          tenantId,
          userId,
          role: isNewTenant ? "owner" : "member",
          createdAt: new Date(),
        })
        .onConflictDoNothing();

      return { tenantId, userId };
    });
  }

  async getUserEmail(userId: string): Promise<string | null> {
    const rows = await db
      .select()
      .from(users)
      .where(eq(users.id, userId))
      .limit(1);
    return rows[0]?.email ?? null;
  }

  async updateTenantName(
    userId: string,
    tenantId: string,
    name: string,
  ): Promise<boolean> {
    const membership = await db
      .select()
      .from(memberships)
      .where(
        and(eq(memberships.userId, userId), eq(memberships.tenantId, tenantId)),
      )
      .limit(1);
    const role = membership[0]?.role;
    if (role !== "owner") {
      return false;
    }
    await db.update(tenants).set({ name }).where(eq(tenants.id, tenantId));
    return true;
  }
}
