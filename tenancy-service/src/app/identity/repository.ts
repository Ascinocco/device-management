import { ResolvedIdentity } from "./dto";

export const IDENTITY_REPOSITORY = "IdentityRepository";

export interface IdentityRepository {
  resolveIdentity(
    clerkUserId: string,
    clerkOrgId: string,
    email: string,
  ): Promise<ResolvedIdentity>;
  getUserEmail(userId: string): Promise<string | null>;
  updateTenantName(
    userId: string,
    tenantId: string,
    name: string,
  ): Promise<boolean>;
}
