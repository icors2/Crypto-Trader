# Playbook: Next.js web app

Use when the user asked for Next.js / App Router specifically. If they have **no** stack preference, prefer `golden-path.md` instead (adds Tailwind/shadcn/Postgres/Vercel opinions).

## Scaffold

Do **not** target `/workspace` or `.` with `create-next-app` if the parent directory is not writable. Scaffold into a subdirectory, then move files up.

```bash
npx create-next-app@latest tmp-scaffold --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```

Add shadcn/ui if the UI is React and they did not name another component library.

## Structure

- App Router under `src/app`
- Shared UI in `src/components`; domain logic outside page files when reusable
- See `assets/reference/project-structure.md`

## Verify

```bash
npm run lint
npm run build
npm run dev   # then browser-check the changed flow
```

## Security

- Validate server actions / route handlers; never trust client input
- Secrets only in env; run threat model (`assets/reference/threat-model.md`) if auth or PII appears
- MCP: `context7` almost always; `vercel` if they deploy there; `playwright` or Chrome DevTools MCP if you will verify in a browser

## After scaffold

- Bind any custom server to `0.0.0.0:$PORT` only if you add one; Next.js handles this.
- Dev server: uncommon port (avoid 3000 / 5173 / 8080 when you can).
- Skills: add verify/deploy skills only if those workflows will repeat.
- Write run/test steps into `AGENTS.md`. Copy CI from `assets/templates/ci/node.yml` if useful.
