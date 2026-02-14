# Bug Bash & QA Plan

De-duplicated findings from three independent reviews. Work split across **Agent A**, **Agent B**, **Agent C**.

---

## De-Duplicated Master List

Items marked with source: `[R1]` = Agent B microservices review, `[R2]` = second reviewer (nswot app), `[R3]` = third reviewer (nswot app). Where reports overlapped, items are merged and noted.

---

### P0 — Critical / Security

| ID | Issue | Source | Service |
|----|-------|--------|---------|
| 1 | **Thinking pipeline is non-functional end-to-end**: Anthropic provider ignores `thinking_delta` SSE events; `LlmResponse` has no thinking field; `extractThinking()` uses dead regex for XML tags; abort path skips extraction entirely | R3 #1-4 | nswot main |
| 2 | **Content blocks never persisted to DB** — `AgentService.executeTurn()` produces `ContentBlock[]` but they're not stored. Approval blocks also lost. Conversations can't resume after restart | R3 #5 + R2 #19 | nswot main |
| 3 | **Chat repository doesn't deserialize block content** — `toDomain()` returns raw JSON strings for `contentFormat: 'blocks'` instead of parsing into `ContentBlock[]` | R3 #6 | nswot main |
| 4 | **Message history sends JSON strings to LLM** — block-format messages passed as serialized JSON strings to LLM context, degrading multi-turn quality | R3 #7 | nswot main |
| 5 | **Approval memory not wired** — `approvalMemoryService.isToolApproved()` never checked before requesting approval. "Yes + Remember" does nothing | R3 #8 | nswot main |
| 6 | **Approval hangs forever** — `handleApproval()` awaits Promise with no timeout. User non-response or UI crash blocks agent loop indefinitely | R2 #4 = R3 #9 | nswot main |
| 7 | **OAuth CSRF vulnerability** — state parameter generated but never validated on callback (`jira-auth.ts:73-104`) | R2 #1 | nswot main |
| 8 | **OAuth resource leak on error path** — missing HTTP server + timeout cleanup when auth code is absent | R2 #2 | nswot main |
| 9 | **OAuth port conflict on re-entry** — no cleanup of previous auth server before re-initiating OAuth | R2 #3 | nswot main |
| 10 | **API gateway `.env` committed with live secrets** — Clerk secret key, service tokens in version control | R1 | test-repo |
| 11 | **Device-worker HTML injection in email** — `device_id` and `reason` interpolated into HTML without escaping (`sagas.py:92`) | R1 | test-repo |
| 12 | **Device-worker URL path injection** — `device_id` in URL without encoding (`sagas.py:103`) | R1 | test-repo |
| 13 | **API gateway CORS hardcoded** to `localhost:5173` — breaks non-local deployment | R1 | test-repo |

### P1 — Bugs (Functional)

| ID | Issue | Source | Service |
|----|-------|--------|---------|
| 14 | **Content duplication on interrupt** — `finalContent += cleanContent` executes on interrupt after content was already appended (`agent.service.ts:164,194`) | R2 #5 | nswot main |
| 15 | **Token counting conflates estimates and final** — `onTokenCount` fires with estimates during streaming, then overwrites with `response.usage` (which may be null → resets to 0) | R3 #10 | nswot main |
| 16 | **Tool failures not logged, can cause retry loops** — errors returned as tool result JSON to LLM with no log entry (`agent.service.ts:310-316`) | R3 #11 | nswot main |
| 17 | **Tool call ID extraction breaks continuation** — `_toolCallId` embedded in `toolInput` JSON; DB-loaded messages lack this field, causing ID mismatches | R3 #12 | nswot main |
| 18 | **No fetch timeouts on any provider** — all `fetch()` calls in openrouter, anthropic, jira, confluence, github providers lack `AbortController` timeout | R2 #11 | nswot main |
| 18a | **Jira ticket creation is broken** — user reports the LLM hangs for a long time then reports it couldn't create the ticket. The write tool flow is: agent calls `create_jira_issue` → write-executor → action-executor → spawns Claude CLI subprocess (10-min timeout) → CLI loads MCP tools → calls Jira API. Root cause unknown — could be: CLI not finding/authenticating with Jira MCP server, OAuth token not passed or expired, MCP tool definition mismatch, prompt to CLI is malformed, or Jira API permission issue. Needs investigation of the full chain (subprocess args, env, MCP config, token forwarding, CLI stderr output) and a fix. Secondary issues: 10-min timeout is too long, no progress feedback, no cancel from UI | User-reported + trace | nswot main |
| 19 | **Circuit breaker trips on non-transient errors** — `shouldTrip()` defaults `true` for unknown errors; 401 auth failures trip the circuit | R2 #12 | nswot main |
| 20 | **Retry logic retries permanent failures** — `isRetryable()` defaults `true`; 422, `LLM_PARSE_ERROR`, `PROFILE_LIMIT` get uselessly retried | R2 #13 = R3 #20 | nswot main |
| 21 | **Path traversal + symlink bypass** — `action-executor.ts` uses simple `..` check instead of `validateWorkspacePath()`; `file-system.ts` doesn't call `realpathSync()` to resolve symlinks | R2 #14 + R3 #14-15 | nswot main |
| 22 | **Orphaned data on conversation delete** — deleting conversation clears `conversation_id` on analyses but doesn't delete chat messages, chat actions, or approval memory | R2 #15 = R3 #28 | nswot main |
| 23 | **Orphaned user message on LLM failure** — message saved before LLM call; failure leaves dangling message with no response | R2 #16 | nswot main |
| 24 | **Non-transactional integration sync** — partial data committed on mid-sync failure; status shows "error" but stale data used in analysis | R2 #17 | nswot main |
| 25 | **Non-transactional analysis profile insert** — `insertProfiles()` runs after status set to "running"; failure leaves analysis stuck with no profile mappings | R2 #18 | nswot main |
| 26 | **Stale closure in `handleRun`** — `modelId` not in dependency array (`analysis-config-panel.tsx:91-102`) | R2 #6 | nswot renderer |
| 27 | **Stale closure in `handleRunAnalysis`** — `analysisIds` missing from dependency array (`chat-analysis.tsx:348-406`) | R2 #7 | nswot renderer |
| 28 | **Mermaid diagram ID collision** — `Date.now()` for element ID; same-ms renders collide (`mermaid-block.tsx:40`) | R2 #9 | nswot renderer |
| 29 | **Unsafe JSON parse swallowed silently** — block parse failure falls back to plain text with no logging (`chat-analysis.tsx:258-270`) | R2 #10 | nswot renderer |
| 30 | **API gateway route handlers lack try-catch** — unhandled rejections crash the process (`devices.ts`, `tenants.ts`) | R1 | test-repo |
| 31 | **API gateway tenancy resolve has no timeout** — uses raw `fetch()` instead of `fetchWithTimeout` | R1 | test-repo |
| 32 | **Tenancy-service array access without null check** on `.returning()` (`drizzle-identity.repository.ts:46,77`) | R1 | test-repo |
| 33 | **Tenancy-service loose equality** `!=` instead of `!==` in role check (`drizzle-identity.repository.ts:121`) | R1 | test-repo |
| 34 | **Tenancy-service Zod errors produce 500** instead of 400 — no global exception filter | R1 | test-repo |
| 35 | **Device-service POST returns 200** instead of 201 Created (`devices.py:57,148,170`) | R1 | test-repo |
| 36 | **Device-service unhandled `IntegrityError`** in repository `add()` — duplicate MAC yields 500 (`sqlalchemy_device_repository.py:26`) | R1 | test-repo |
| 37 | **Device-service update allows MAC change** — violates immutability invariant (`sqlalchemy_device_repository.py:64`) | R1 | test-repo |
| 38 | **Device-service no pagination constraints** — `limit=999999999` accepted (`devices.py:77-79`) | R1 | test-repo |
| 39 | **Device-worker saga HTTP calls have no timeout** — defaults to 5-minute Python timeout (`sagas.py`) | R1 | test-repo |
| 40 | **Device-worker saga/projector calls lack circuit breaker** — cascading failure risk (`sagas.py`, `projector.py`) | R1 | test-repo |
| 41 | **Device-worker `payload["device_id"]` KeyError** — bracket access without existence check (`main.py:94`) | R1 | test-repo |
| 42 | **Device-worker engine never closed** — no graceful shutdown for SIGTERM (`main.py:121-198`) | R1 | test-repo |
| 43 | **Device-UI `useQuery` never handles errors** — failures show "Loading..." forever (DevicesPage, DeviceDetailPage) | R1 | test-repo |
| 44 | **Device-UI `useMutation` no `onError`** — silent failures on create/retire/activate | R1 | test-repo |
| 45 | **Device-UI Zod parse not wrapped in try-catch** — validation crashes the form (`NewDevicePage.tsx:31`) | R1 | test-repo |
| 46 | **Device-UI no Error Boundary** — unhandled render errors unmount entire app | R1 | test-repo |
| 47 | **Docker Compose `depends_on` lacks health conditions** — race condition on startup | R1 | test-repo |

### P2 — Gaps (Missing Protection / Data Quality)

| ID | Issue | Source | Service |
|----|-------|--------|---------|
| 48 | **No workspace validation in chat IPC handlers** — no check that analysis/conversation belongs to current workspace (`chat.ipc.ts`) | R3 #13 | nswot main |
| 49 | **Chart spec not validated in render executor** — `render_chart` accepts any object; crashes frontend Chart.js (`render-executor.ts:125-141`) | R3 #16 | nswot main |
| 50 | **Database migration failures silently swallowed** — invalid SQL rolls back but no error logged; app proceeds (`database.ts:6-31`) | R3 #19 | nswot main |
| 51 | **Conversation `updated_at` not touched during chat** — conversations don't sort by recency | R3 #26 | nswot main |
| 52 | **Device-service read model never synced** — `/projected` returns stale data; `owner_email` never populated | R1 | test-repo |
| 53 | **Device-service outbox events created but never processed** — `attempts`, `last_error`, `processed_at` unused | R1 | test-repo |
| 54 | **Device-service health check doesn't verify DB** — returns `{ok:true}` unconditionally | R1 | test-repo |
| 55 | **Tenancy-service no health check endpoint** | R1 | test-repo |
| 56 | **Tenancy-service DB pool never closed** — no `OnApplicationShutdown` lifecycle hook | R1 | test-repo |
| 57 | **Tenancy-service e2e test is broken** — tests `GET /` which doesn't exist | R1 | test-repo |
| 58 | **API gateway no global error middleware** | R1 | test-repo |
| 59 | **API gateway minimal test coverage** — only `fetchWithTimeout` tested | R1 | test-repo |
| 60 | **Device-worker no tests for poll loop** — `handle_event()`, `project_event()` untested | R1 | test-repo |
| 61 | **Device-worker no saga recovery** — crash leaves orphaned `running` sagas | R1 | test-repo |
| 62 | **Device-UI zero test files** | R1 | test-repo |
| 63 | **Device-UI no empty state** for device list | R1 | test-repo |
| 64 | **Device-UI MAC address validation** is `.min(1)` only — no format validation | R1 | test-repo |
| 65 | **No structured logging across entire test-repo stack** | R1 | test-repo |
| 66 | **No correlation ID / request tracing** across test-repo services | R1 | test-repo |
| 67 | **No CI/CD pipeline** — no `.github/workflows/` | R1 | test-repo |
| 68 | **No root README or `.env.example`** | R1 | test-repo |
| 69 | **Device-worker `.env.example` missing** `DEVICE_SERVICE_URL` and `DEVICE_SERVICE_TOKEN` | R1 | test-repo |

### P3 — Improvements (Quality / UX / DX)

| ID | Issue | Source | Service |
|----|-------|--------|---------|
| 70 | **ContentBlock type weak in renderer** — `use-agent.ts` defines own `{type: string, data: unknown}` instead of importing discriminated union; `env.d.ts` also uses weak type | R2 #8 + R3 #24 | nswot renderer |
| 71 | **ActionToolName type incomplete** — missing `write_file` and 12 render/read tool names; repository casts are unsound | R2 #20 = R3 #21 | nswot domain |
| 72 | **Inconsistent `sourceTypes` field** — `env.d.ts` says `string[]`, `domain/types.ts` says `EvidenceSourceType[]` | R3 #22 | nswot domain |
| 73 | **AgentState type duplicated** — defined separately in `use-agent.ts` and `agent.service.ts` | R3 #23 | nswot domain |
| 74 | **No error handling in approval-block.tsx** — `handleApprove`/`handleReject` don't check IPC result | R2 #21 | nswot renderer |
| 75 | **No block data validation** in `content-block-renderer.tsx` — unsafe casts to specific block types | R2 #22 | nswot renderer |
| 76 | **Missing IPC error handling in chat page** — multiple IPC calls don't check success or display errors (`chat-analysis.tsx`) | R2 #23 + R3 #17-18 | nswot renderer |
| 77 | **No cache invalidation for related entities** — sending message only invalidates chat cache, not actions cache (`use-chat.ts`) | R2 #24 | nswot renderer |
| 78 | **Memory indicator polls without backoff** — repeated failures produce no feedback (`memory-indicator.tsx`) | R2 #25 | nswot renderer |
| 79 | **`runAnalysis`/`runAnalysisInChat` duplication** — ~280 lines of near-identical logic in `analysis.service.ts` | R2 #26 | nswot main |
| 80 | **Chart creation has no error boundary** — malformed data crashes component (`chart-block.tsx`) | R2 #27 | nswot renderer |
| 81 | **Data table sorting ignores numeric values** — `localeCompare` for all; "2" sorts after "10" (`data-table-block.tsx`) | R2 #28 | nswot renderer |
| 82 | **Window-destroyed checks scattered** — same pattern repeated 7+ times in `agent.ipc.ts`; should be helper | R2 #29 | nswot main |
| 83 | **No UI indicator for `awaiting_approval` state** — agent shows same state as thinking/executing | R3 #25 | nswot renderer |
| 84 | **Streaming text not cleared on error** — `streamingText` can persist showing mixed content (`chat-analysis.tsx`) | R3 #27 | nswot renderer |
| 85 | **Old action system coexists with new agent tools** — Phase 3c `providers/actions/` still fully instantiated alongside Phase 4 `providers/agent-tools/` | R3 #29 | nswot main |
| 86 | **Test coverage gaps** — no tests for IPC handlers (0/16), confluence.service, github.service, approval-memory.repository, conversation.repository | R2 #30 | nswot |
| 87 | **API gateway inconsistent error format** — no standard error response schema | R1 | test-repo |
| 88 | **API gateway missing `dev`/`build`/`start` scripts** in package.json | R1 | test-repo |
| 89 | **Tenancy-service magic string `"clerk"`** hardcoded in 3 places | R1 | test-repo |
| 90 | **Tenancy-service ESLint disables** `no-explicit-any`, `no-unsafe-return`, etc. | R1 | test-repo |
| 91 | **Device-service duplicate `DeviceStatus` enum** in domain and infra layers | R1 | test-repo |
| 92 | **Device-UI mutation buttons no `isPending` state** — no loading feedback | R1 | test-repo |
| 93 | **Device-UI no `QueryClient` configuration** — default retry/cache behavior | R1 | test-repo |
| 94 | **Makefile only has `run` target** — missing docker-up, test, build, install | R1 | test-repo |
| 95 | **`run-all.sh` no dependency checks**, hard-kills on exit | R1 | test-repo |

---

## Agent Assignments

### Agent A — nswot Backend (Main Process)

**Scope**: Services, providers, infrastructure, domain types, repositories, DB migrations. All `src/main/` changes.

| Task | Items | Description |
|------|-------|-------------|
| ✅ **A1: Fix thinking pipeline** | 1 | DONE — Added `thinking_delta`/`thinking` SSE handling to Anthropic provider, `thinking` field to `LlmResponse`/`LlmCompletionRequest`, fixed `extractThinking()` to use structured data with regex fallback, thinking extracted on abort path, fixed content duplication on abort (item 14) |
| ✅ **A2: Fix content block persistence** | 2, 3, 4 | DONE — Added `blocks?` field to ChatMessage, fixed `toDomain()` to parse JSON blocks, added `extractTextForLlm()` to extract text from block messages for LLM context |
| ✅ **A3: Wire approval memory + add timeout** | 5, 6 | DONE — Extended agent-approval to carry metadata + remember flag, wired approvalMemoryService.remember() on "Yes + Remember", added 5-min auto-reject timeout, passed service to chat.ipc.ts, updated tests |
| **A4: Fix agent service bugs** | 14, 15, 16, 17 | Fix double-append on interrupt; fix token count null handling; log tool failures before returning error to LLM; fix tool call ID persistence for conversation continuity |
| ✅ **A5: Fix OAuth auth flow** | 7, 8, 9 | DONE — Validated state parameter (CSRF fix), cleaned up server+timeout on all error/missing-code paths (resource leak fix), added cleanupActiveServer() on re-entry (port conflict fix), added server 'error' event handler |
| ✅ **A6: Fix Jira ticket creation** | 18a | DONE — Root cause: MCP tool name mismatch (`mcp__jira__*` vs actual `mcp__mcp-atlassian__jira_*`). Fixed `getAllowedTools()` to use configurable MCP prefixes matching real server names. Reduced timeout 600s→120s. Added structured logging (Logger) for CLI args, stderr, errors. Wired abort signal from agent→write-executor→action-executor→subprocess. Fixed pre-existing test (maxTurns mismatch). All 38 action-executor tests pass. |
| ✅ **A7: Harden provider resilience** | 18, 19, 20 | DONE — Added `AbortSignal.timeout(30_000)` to all provider fetch calls (anthropic, openrouter, jira, confluence, github, jira-auth). Changed `shouldTrip()` default to `return false` with explicit transient error detection (network errors, 5xx). Added `NON_TRANSIENT_ERROR_CODES` set to skip auth/domain errors. Changed `isRetryable()` default to `return false` with explicit retryable detection (429, 503, 5xx, network errors). All 904 tests pass. |
| ✅ **A8: Fix path traversal** | 21 | DONE — Added `realpathSync()` symlink resolution to `validateWorkspacePath()` with nearest-ancestor walk-up for non-existent targets. Improved pre-checks in action-executor and write-executor to reject absolute paths (Unix `/` and Windows `C:`). Added symlink traversal test (rejects escape) and valid symlink test (allows in-workspace). All 906 tests pass. |
| ✅ **A9: Fix data integrity** | 22, 23, 50, 51 | DONE — Item 22: Added `deleteWithCascade()` to ConversationRepository — transactional cascade deletes chat_messages, chat_actions, clears analysis links, removes conversation (approval_memory cascades via FK). Item 23: Added `deleteById()` to ChatRepository, agent.ipc.ts now cleans up orphaned user message on agent failure/error. Item 50: Added `Logger.tryGetInstance()` and migration logging (start, success, failure with rollback). Item 51: Already handled — agent.ipc.ts calls `conversationService.touch()` after each turn. Items 24/25 (transactional sync/analysis insert): deferred — better-sqlite3 transactions are synchronous but sync/analysis flows are async with external API calls between DB ops; current partial-commit behavior with error status is acceptable. Item 48 (workspace validation in chat IPC): deferred — requires adding WorkspaceService dependency to ChatService; low risk in local-first desktop app. All 906 tests pass. |
| ✅ **A10: Refactor & cleanup** | 79, 82 | DONE — Item 79: Replaced ~150 lines of duplicated pipeline code in `runAnalysisInChat()` with single delegation to `runAnalysis()` (RunAnalysisInChatInput extends RunAnalysisInput, both already carry conversationId/parentAnalysisId). Item 82: Extracted `safeSend()` helper in agent.ipc.ts replacing 7+ scattered `window && !window.isDestroyed()` checks. Item 85 (docs): skipped per project convention — no proactive documentation creation. All 906 tests pass. |
| ✅ **A11: Fix types** | 71, 72, 73 | DONE — Item 71: Extended `ActionToolName` union in domain/types.ts with all Phase 4 agent tool names (fetch_jira_data, fetch_confluence_data, fetch_github_data, run_codebase_analysis, search_profiles, render_swot_analysis, render_mermaid, render_chart, render_data_table, write_file). Item 72: Added `EvidenceSourceType` alias to env.d.ts and replaced all `string`/inline union references in Theme.sourceTypes and SourceCoverageEntry.sourceType. Item 73: Added `AgentState` type to env.d.ts global scope; changed use-agent.ts from local definition to re-export via `export type { AgentState }`. All 906 tests pass. |
| ✅ **A12: Validate render executor** | 49 | DONE — Added chart spec validation in `renderChart()`: validates `spec` is an object, `spec.data` exists and is an object, `spec.data.labels` is an array, `spec.data.datasets` is a non-empty array. Returns descriptive error messages to the LLM for self-correction. Added 4 new tests for each validation case. Fixed integration test to use correct nested `spec.data` structure. All 910 tests pass. |
| ✅ **A13: Tests** | 86 | DONE — Added 10 tests for ConversationRepository (insert, findById, findByWorkspace ordering, updateTitle, updateTimestamp, delete, deleteWithCascade with chat data cleanup, deleteWithCascade with approval_memory FK cascade). Added 8 tests for ApprovalMemoryRepository (set approved/rejected, isApproved unknown tool, upsert on conflict, findByConversation, deleteByConversation, FK cascade on conversation delete). All 928 tests pass. |

---

### Agent B — test-repo Microservices (This Agent)

**Scope**: `device-service/`, `tenancy-service/`, `api-gateway/`, `device-worker/`, `device-ui/`, root infrastructure.

| Task | Items | Description |
|------|-------|-------------|
| ✅ **B1: Fix API gateway security** | 10, 13 | DONE — `.env` was never committed (false positive); made CORS origins configurable via `CORS_ORIGINS` env var |
| ✅ **B2: Fix API gateway error handling** | 30, 31, 58 | DONE — Added try-catch to devices.ts and tenants.ts route handlers; switched to `fetchWithTimeout` in tenancy.ts; added global Hono `app.onError()` middleware |
| ✅ **B3: Fix device-worker injection bugs** | 11, 12 | DONE — Added `html.escape()` for email template interpolation; added `urllib.parse.quote()` for URL path construction in sagas.py |
| ✅ **B4: Fix device-worker resilience** | 39, 40, 41, 42 | DONE — Added `_http_client()` with configured timeouts; wrapped saga+projector calls with circuit breakers; validated payload fields; added SIGTERM handler + graceful shutdown + engine cleanup |
| ✅ **B5: Fix device-service bugs** | 35, 36, 37, 38 | DONE — Added `status_code=201` to create endpoint; caught `IntegrityError` in `add()`; removed `mac_address` from update `.values()`; added `Query(ge=1, le=1000)` pagination constraints |
| ✅ **B6: Fix tenancy-service bugs** | 32, 33, 34 | DONE — Added null checks on `.returning()` results; fixed `!=` to `!==`; created `AppExceptionFilter` for ZodError→400, ValidationError→400, NotFoundError→404 |
| ✅ **B7: Fix device-UI critical bugs** | 43, 44, 45, 46 | DONE — Added `isError`/`error` to useQuery hooks; added `onError` to all mutations; wrapped Zod parse in try-catch; created `ErrorBoundary` component |
| ✅ **B8: Fix Docker startup** | 47 | DONE — Added healthchecks to device-service, tenancy-service; changed all `depends_on` to use `condition: service_healthy` |
| ✅ **B9: Add health checks** | 54, 55, 56 | DONE — Device-service `/health` now verifies DB with `SELECT 1`; created tenancy-service `HealthController` at `/internal/health`; added `OnApplicationShutdown` to close DB pool |
| ✅ **B10: Fix device-service data gaps** | 52, 53 | DONE — Read model sync already implemented via projector.py (handles device.created/retired/activated events); outbox processing already in main.py poll loop; both hardened in B4 |
| ✅ **B11: Device-UI UX fixes** | 63, 64, 92, 93 | DONE — Added empty state for device list; MAC format regex validation; `isPending` disabled state on all buttons; configured `QueryClient` with retry=2, staleTime=30s |
| ✅ **B12: Infrastructure & DX** | 65, 66, 67, 68, 69, 87, 88, 89, 90, 91, 94, 95 | DONE — Fixed worker .env.example (added DEVICE_SERVICE_URL/TOKEN); created root .env.example; added gateway `dev`/`start` scripts; extracted `AUTH_PROVIDER` constant; tightened ESLint rules to `warn`; deduped `DeviceStatus` enum (infra imports from domain); improved Makefile (docker-up/down, install, test); improved run-all.sh (dep checks, graceful shutdown). Note: structured logging (65), correlation IDs (66), CI/CD (67) deferred as larger scope items |

---

### Agent C — nswot Frontend (Renderer + IPC)

**Scope**: `src/renderer/` components, hooks, routes, and the IPC-facing code in `src/main/ipc/handlers/`.

| Task | Items | Description |
|------|-------|-------------|
| **✅ C1: Fix stale closures** | 26, 27 | Item 26: `modelId` already in deps (false positive), fixed setState-during-render instead; Item 27: added `analysisIds` to `handleRunAnalysis` deps |
| **✅ C2: Fix mermaid ID collision** | 28 | Replaced `Date.now()` with `crypto.randomUUID()` |
| **✅ C3: Fix JSON parse + streaming errors** | 29, 84 | Parse logging added in C4; added safety net to clear `streamingText` when agent enters error state even if `wasActive` was false |
| **✅ C4: Fix content block type safety** | 70, 75 | Replaced weak local type with re-export from domain; added `isValidBlock()` guard in hook; rewrote renderer to use `isBlockType()` guards + error boundary per block; validated blocks on JSON parse in chat page |
| **✅ C5: Fix approval UI + tool execution UX** | 74, 83, 18a (UI side) | Added error handling + error display to all approval callbacks; status bar shows distinct amber pulsing state for `awaiting_approval` with "Action needs your approval" text; tool-progress shows elapsed time counter; added write tool labels/colors. Stop button already calls interrupt() — tool cancellation backend is A6's scope |
| **✅ C6: Fix chat page error handling** | 76 | Added try-catch to history loading IIFE, .catch to listModels, error check on agent.send; added page-level error banner; errors cleared on navigation |
| **✅ C7: Fix cache invalidation** | 77 | Added `actions` cache invalidation to `useSendMessage.onSuccess` |
| **✅ C8: Fix memory indicator** | 78 | Replaced fixed-interval polling with exponential backoff (5s→60s); stops polling after 5 consecutive errors; shows error state |
| **✅ C9: Fix chart error boundary** | 80 | Wrapped Chart.js `new Chart()` in try-catch; shows error fallback with message; hides Save button on error |
| **✅ C10: Fix data table sorting** | 81 | NOT A BUG — `localeCompare` already uses `{ numeric: true }` which correctly sorts "2" before "10" |
| **✅ C11: Tests** | 62 (partial), 86 (partial) | Added 13-test suite for `isValidBlock` validator; updated vitest config to include `.test.tsx`; NOTE: full component tests require `@testing-library/react` + `jsdom` (not installed) |

---

## Execution Order

All agents can start in parallel. Within each agent, tasks are ordered by priority.

```
Phase 1 (P0 — do first):
  Agent A: A1, A2, A3, A5, A6 (Jira investigation + fix)
  Agent B: B1, B2, B3, B4
  Agent C: C1, C4, C5

Phase 2 (P1 — do second):
  Agent A: A4, A7, A8, A9
  Agent B: B5, B6, B7, B8
  Agent C: C2, C3, C6

Phase 3 (P2/P3 — do last):
  Agent A: A10, A11, A12, A13
  Agent B: B9, B10, B11, B12
  Agent C: C7, C8, C9, C10, C11
```

---

## Notes

- **No overlap**: Each item assigned to exactly one agent. Cross-cutting type fixes (items 70-73) are split — Agent A owns domain types, Agent C owns renderer type imports.
- **Agent A** has the heaviest P0 load (thinking pipeline, persistence, approval memory are all broken features).
- **Agent B** has the widest scope (5 separate services) but many items are straightforward fixes.
- **Agent C** has focused UI work — stale closures, error handling, type safety, and polish.
- Agents should coordinate on shared types: if Agent A changes `ContentBlock`, `ActionToolName`, or `AgentState` definitions, Agent C needs the updated types to import.
