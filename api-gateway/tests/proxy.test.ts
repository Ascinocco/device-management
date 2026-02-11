import { describe, it, expect } from "vitest";
import { fetchWithTimeout } from "../src/fetch-with-timeout";

describe("fetchWithTimeout", () => {
  it("returns upstream response when within timeout", async () => {
    // Mock a fast response using a data URL
    const res = await fetchWithTimeout(
      "data:application/json,{\"ok\":true}",
      { method: "GET" },
      5000
    );

    expect(res.status).toBe(200);
  });

  it("returns 504 when request exceeds timeout", async () => {
    // Use an AbortController-aware approach: create a server that never responds
    // For unit test, we mock fetch to simulate a slow response
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async (_url: string, init?: RequestInit) => {
      // Simulate a request that takes longer than timeout
      return new Promise<Response>((resolve, reject) => {
        const timer = setTimeout(() => resolve(new Response("ok")), 60000);
        init?.signal?.addEventListener("abort", () => {
          clearTimeout(timer);
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      });
    }) as typeof fetch;

    try {
      const res = await fetchWithTimeout(
        "http://slow-server.test/api",
        { method: "GET" },
        50 // 50ms timeout
      );

      expect(res.status).toBe(504);
      const body = await res.json();
      expect(body.error).toBe("upstream timeout");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("re-throws non-abort errors", async () => {
    const originalFetch = globalThis.fetch;

    globalThis.fetch = (async () => {
      throw new Error("Network failure");
    }) as typeof fetch;

    try {
      await expect(
        fetchWithTimeout("http://fail.test", { method: "GET" }, 5000)
      ).rejects.toThrow("Network failure");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
