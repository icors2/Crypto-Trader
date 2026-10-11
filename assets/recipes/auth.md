# Recipe: Auth

**Sensitive:** yes — always run `security-review` after wiring.

## Goal

Users can sign up / sign in and a protected route rejects anonymous access.

## Defaults (if unset)

- Next.js / Vite web: Auth.js, Clerk, Supabase Auth, or NextAuth-compatible — pick what matches the DB/host already chosen.
- API-only: session tokens or JWT issued by your API; do not invent a custom crypto scheme.

Confirm with the user if more than one option fits.

## Minimum slice

1. Provider configured with env **names** in `.env.example` (e.g. `AUTH_SECRET`, `GOOGLE_CLIENT_ID`).
2. Sign-in UI or documented CLI/API login path.
3. One protected page or route that redirects/401s when logged out.
4. Sign-out works.

Out of scope for v1 unless asked: roles admin UI, SSO, SCIM, passkeys, multi-tenant orgs.

## Security

- Secrets only server-side; never expose client secrets in the browser bundle.
- Secure cookies (`HttpOnly`, `Secure`, `SameSite`) when using cookies.
- Authorize per resource after authenticate (see `assets/checklists/security-review.md`).
- Password reset / magic links single-use and time-limited.

## Verify

- Logged-out user cannot reach the protected route
- Logged-in user can
- `security-review` on the auth files

## MCP

Optional: vendor MCP (e.g. `supabase`) only if the agent will manage the project via tools.
