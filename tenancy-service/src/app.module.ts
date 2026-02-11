import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";

import { IdentityController } from "./delivery/identity/identity.controller";
import { InternalGuard } from "./delivery/auth/internal.guard";
import { IdentityApplicationService } from "./app/identity/service";
import { DrizzleIdentityRepository } from "./infra/identity/drizzle-identity.repository";
import { IDENTITY_REPOSITORY } from "./app/identity/repository";

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true })],
  controllers: [IdentityController],
  providers: [
    InternalGuard,
    { provide: IDENTITY_REPOSITORY, useClass: DrizzleIdentityRepository },
    IdentityApplicationService,
  ],
})
export class AppModule {}
