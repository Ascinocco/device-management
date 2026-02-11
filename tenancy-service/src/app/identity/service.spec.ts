import { IdentityApplicationService } from "./service";
import { ValidationError } from "../contracts";
import type { IdentityRepository } from "./repository";

function mockRepo(): IdentityRepository {
  return {
    resolveIdentity: jest.fn().mockResolvedValue({
      userId: "user-1",
      tenantId: "tenant-1",
    }),
    getUserEmail: jest.fn().mockResolvedValue("user@example.com"),
    updateTenantName: jest.fn().mockResolvedValue(true),
  };
}

describe("IdentityApplicationService", () => {
  let service: IdentityApplicationService;
  let repo: jest.Mocked<IdentityRepository>;

  beforeEach(() => {
    repo = mockRepo() as jest.Mocked<IdentityRepository>;
    service = new IdentityApplicationService(repo);
  });

  describe("resolve", () => {
    it("returns userId and tenantId on success", async () => {
      const result = await service.resolve({
        clerkUserId: "clerk_1",
        clerkOrgId: "org_1",
        email: "user@example.com",
      });

      expect(result).toEqual({ userId: "user-1", tenantId: "tenant-1" });
      expect(repo.resolveIdentity).toHaveBeenCalledWith(
        "clerk_1",
        "org_1",
        "user@example.com"
      );
    });

    it("throws ValidationError when clerkUserId is missing", async () => {
      await expect(
        service.resolve({
          clerkUserId: "",
          clerkOrgId: "org_1",
          email: "user@example.com",
        })
      ).rejects.toThrow(ValidationError);
    });

    it("throws ValidationError when clerkOrgId is missing", async () => {
      await expect(
        service.resolve({
          clerkUserId: "clerk_1",
          clerkOrgId: "",
          email: "user@example.com",
        })
      ).rejects.toThrow(ValidationError);
    });

    it("throws ValidationError when email is missing", async () => {
      await expect(
        service.resolve({
          clerkUserId: "clerk_1",
          clerkOrgId: "org_1",
          email: "",
        })
      ).rejects.toThrow(ValidationError);
    });
  });

  describe("getUserEmail", () => {
    it("returns email when found", async () => {
      const result = await service.getUserEmail("user-1");
      expect(result).toBe("user@example.com");
    });

    it("returns null when not found", async () => {
      repo.getUserEmail.mockResolvedValue(null);
      const result = await service.getUserEmail("unknown");
      expect(result).toBeNull();
    });
  });

  describe("updateTenantName", () => {
    it("succeeds when repo returns true", async () => {
      await expect(
        service.updateTenantName({
          tenantId: "tenant-1",
          userId: "user-1",
          name: "New Name",
        })
      ).resolves.toBeUndefined();
    });

    it("throws ValidationError when repo returns false (forbidden)", async () => {
      repo.updateTenantName.mockResolvedValue(false);

      await expect(
        service.updateTenantName({
          tenantId: "tenant-1",
          userId: "user-1",
          name: "New Name",
        })
      ).rejects.toThrow(ValidationError);
    });

    it("throws ValidationError when name is empty", async () => {
      await expect(
        service.updateTenantName({
          tenantId: "tenant-1",
          userId: "user-1",
          name: "",
        })
      ).rejects.toThrow(ValidationError);
    });
  });
});
