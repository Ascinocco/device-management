export type ResolveIdentityCommand = {
  clerkUserId: string;
  clerkOrgId: string;
  email: string;
};

export type UpdateTenantNameCommand = {
  userId: string;
  tenantId: string;
  name: string;
};

export type ResolvedIdentity = {
  userId: string;
  tenantId: string;
};
