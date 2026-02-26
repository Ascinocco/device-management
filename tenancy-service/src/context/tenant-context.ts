import { AsyncLocalStorage } from "node:async_hooks";
import { Request, Response, NextFunction } from "express";
import { verify } from "jsonwebtoken";

interface TenantContext {
  tenantId: string;
  tenantName: string;
  plan: "starter" | "professional" | "enterprise";
  features: string[];
}

const tenantStorage = new AsyncLocalStorage<TenantContext>();

export function getTenantContext(): TenantContext | undefined {
  return tenantStorage.getStore();
}

export function requireTenantContext(): TenantContext {
  const ctx = tenantStorage.getStore();
  if (\!ctx) {
    throw new Error("Tenant context not available. Ensure tenantMiddleware is applied.");
  }
  return ctx;
}

export function tenantMiddleware(jwtSecret: string) {
  return (req: Request, _res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (\!authHeader?.startsWith("Bearer ")) {
      return next(new Error("Missing or invalid authorization header"));
    }

    const token = authHeader.slice(7);

    try {
      const decoded = verify(token, jwtSecret) as {
        tenant_id: string;
        tenant_name: string;
        plan: string;
        features: string[];
      };

      const context: TenantContext = {
        tenantId: decoded.tenant_id,
        tenantName: decoded.tenant_name,
        plan: decoded.plan as TenantContext["plan"],
        features: decoded.features ?? [],
      };

      tenantStorage.run(context, () => next());
    } catch (err) {
      next(new Error("Invalid or expired tenant token"));
    }
  };
}

