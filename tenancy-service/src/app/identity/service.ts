import { Inject, Injectable } from "@nestjs/common";

import { ValidationError } from "../contracts";
import {
  ResolveIdentityCommand,
  ResolvedIdentity,
  UpdateTenantNameCommand,
} from "./dto";
import { IDENTITY_REPOSITORY, type IdentityRepository } from "./repository";

@Injectable()
export class IdentityApplicationService {
  constructor(
    @Inject(IDENTITY_REPOSITORY) private readonly repo: IdentityRepository,
  ) {}

  async resolve(cmd: ResolveIdentityCommand): Promise<ResolvedIdentity> {
    if (!cmd.clerkUserId || !cmd.clerkOrgId || !cmd.email) {
      throw new ValidationError("Missing clerk ids");
    }
    return this.repo.resolveIdentity(
      cmd.clerkUserId,
      cmd.clerkOrgId,
      cmd.email,
    );
  }

  async getUserEmail(userId: string): Promise<string | null> {
    return this.repo.getUserEmail(userId);
  }

  async updateTenantName(cmd: UpdateTenantNameCommand): Promise<void> {
    if (!cmd.userId || !cmd.tenantId || !cmd.name) {
      throw new ValidationError("Missing tenant update fields");
    }
    const updated = await this.repo.updateTenantName(
      cmd.userId,
      cmd.tenantId,
      cmd.name,
    );
    if (!updated) {
      throw new ValidationError("Forbidden");
    }
  }
}
