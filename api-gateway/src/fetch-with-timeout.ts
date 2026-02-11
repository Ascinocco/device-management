/**
 * fetch() wrapper that enforces a timeout budget via AbortController.
 * If the upstream doesn't respond within `timeoutMs`, the request is
 * aborted and a 504 Gateway Timeout is returned to the caller.
 */
export async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return new Response(
        JSON.stringify({ error: "upstream timeout" }),
        { status: 504, headers: { "content-type": "application/json" } }
      );
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
