# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from `frontend/`.

```bash
npm run dev       # dev server on :5173
npm run build     # tsc type-check + vite build
npm run preview   # serve the dist/ build locally
```

There is no test suite — verify UI changes by running the dev server.

## Architecture

**Stack:** React 18 + TypeScript + React Router v6 + Vite. No state-management library; global auth state lives in a single React context.

**API base URL** is `import.meta.env.VITE_API_URL` (falls back to `http://localhost:8000`). All HTTP calls go through `src/api/client.ts`, which exports thin `get` / `post` / `del` / `patch` helpers. `ApiError` (carries `.status`) is thrown on non-OK responses.

**Auth:** `src/store/auth.tsx` is a `Context` + `localStorage` store (`static:token`). The token is a JWT access token from the backend. `useAuth()` returns `{ token, setToken, clearToken }`. Route protection is handled by `<Protected>` in `App.tsx` — unauthenticated users are redirected to `/login`.

**Routing** (`App.tsx`): public routes are `/login` and `/register`; everything else is wrapped in `<Protected>`. The `/invite` route is intentionally public (cipher key flow).

**Domain vocabulary** (matches backend — use these terms in code):

| Term | Meaning |
|------|---------|
| `Channel` | A chat room |
| `Contact` | Membership in a Channel; has a `callsign` |
| `Callsign` | Anonymous in-channel pseudonym |
| `Controller` | Channel creator (role) |
| `Transmission` | A message |
| `Cipher Key` | Single-use invite token for encrypted channels |

**WebSocket hook** (`src/lib/useChannelSocket.ts`): handles the full connection lifecycle — mints a one-shot socket token via `POST /auth/socket-token` before each connection, exponential-backoff reconnect (500 ms × 2ⁿ, cap 30 s, 8 retries), and fires `onReconnect(lastSeenId)` so the caller can backfill missed transmissions. Close codes `4001`/`4003` are terminal (no retry).

**Styling:** single global stylesheet at `src/index.css`. No CSS modules or Tailwind. Design tokens are CSS custom properties on `:root` (`--bg`, `--surface`, `--accent` #ffb000, `--text`, `--muted`, etc.). The monospace font stack is `Share Tech Mono → IBM Plex Mono`. Shared primitives: `.btn`, `.btn-primary`, `.btn-ghost`, `.btn-danger`, `.btn-sm`, `.input`, `.error-msg`. Auth pages use `.auth-page` / `.auth-card` / `.auth-form`.

**API layer** (`src/api/`):
- `types.ts` — all shared TypeScript interfaces; `WsMessage` is the canonical WebSocket frame union
- `auth.ts` — `register`, `login`, `getSocketToken`
- `channels.ts` — channel CRUD + contact/transmission operations

**`pendingCipherKey`** — `sessionStorage` key used to preserve a cipher key token across the login redirect so the user lands on the invite page after authenticating.
