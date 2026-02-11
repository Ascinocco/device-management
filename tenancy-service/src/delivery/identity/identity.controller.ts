import {
  Body,
  Controller,
  Get,
  Param,
  Patch,
  Post,
  UseGuards,
} from "@nestjs/common";
import { z } from "zod";

import { InternalGuard } from "../auth/internal.guard";
import { IdentityApplicationService } from "../../app/identity/service";

const resolveSchema = z.object({
  clerkUserId: z.string(),
  clerkOrgId: z.string(),
  email: z.email(),
});

const updateTenantSchema = z.object({
  userId: z.string(),
  name: z.string().min(1),
});

@UseGuards(InternalGuard)
@Controller("internal")
export class IdentityController {
  constructor(private readonly service: IdentityApplicationService) {}

  @Post("resolve")
  async resolve(@Body() body: unknown) {
    const parsed = resolveSchema.parse(body);
    return this.service.resolve(parsed);
  }

  @Get("user-email/:userId")
  async getUserEmail(@Param("userId") userId: string) {
    const email = await this.service.getUserEmail(userId);
    if (!email) {
      return { email: null };
    }
    return { email };
  }

  @Patch("tenants/:tenantId/name")
  async updateTenantName(
    @Param("tenantId") tenantId: string,
    @Body() body: unknown,
  ) {
    const parsed = updateTenantSchema.parse(body);
    await this.service.updateTenantName({
      tenantId,
      userId: parsed.userId,
      name: parsed.name,
    });
    return { ok: true };
  }
}
