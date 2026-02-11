import { CanActivate, ExecutionContext, Injectable } from "@nestjs/common";

import { settings } from "../../app/settings";

@Injectable()
export class InternalGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const req = context
      .switchToHttp()
      .getRequest<{ headers: Record<string, string | undefined> }>();
    const token = req.headers["x-internal-token"];
    return token === settings.tenancyServiceToken;
  }
}
