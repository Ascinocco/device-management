import { WebSocket } from "ws";
import { verify } from "jsonwebtoken";

interface TenantClaims {
  tenant_id: string;
  sub: string;
  permissions: string[];
}

/**
 * Validates that a WebSocket subscription request is scoped
 * to the authenticated tenant. Prevents cross-tenant data leakage
 * by extracting tenant_id from the JWT rather than trusting
 * client-provided channel identifiers.
 */
export function validateTenantSubscription(
  ws: WebSocket,
  channelId: string,
  token: string,
  jwtSecret: string
): { valid: boolean; tenantId?: string; error?: string } {
  try {
    const claims = verify(token, jwtSecret) as TenantClaims;
    const expectedPrefix = `tenant:${claims.tenant_id}:`;

    if (\!channelId.startsWith(expectedPrefix)) {
      return {
        valid: false,
        error: `Channel ${channelId} does not belong to tenant ${claims.tenant_id}`,
      };
    }

    return { valid: true, tenantId: claims.tenant_id };
  } catch {
    return { valid: false, error: "Invalid or expired authentication token" };
  }
}

/**
 * Wraps the subscription handler with tenant validation.
 * Drop-in replacement for the existing subscribeToDeviceEvents.
 */
export function createTenantScopedHandler(jwtSecret: string) {
  return (ws: WebSocket, channelId: string, token: string) => {
    const result = validateTenantSubscription(ws, channelId, token, jwtSecret);

    if (\!result.valid) {
      ws.send(JSON.stringify({ error: "FORBIDDEN", message: result.error }));
      ws.close(4003, "Tenant isolation violation");
      return;
    }

    // Proceed with tenant-scoped subscription
    return { tenantId: result.tenantId, channelId };
  };
}

