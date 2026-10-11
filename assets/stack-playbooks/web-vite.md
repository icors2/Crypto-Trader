# Playbook: Vite + React

Use for a static page, toy, or game, or when they asked for Vite.

## Scaffold

```bash
npm create vite@latest tmp-scaffold -- --template react-ts
```

Move generated files to the repo root if this starter is still empty of app code. Add Tailwind and shadcn/ui when they did not name another component library.

## Structure

- Keep `src/` as Vite created it; feature folders if the UI grows
- See `assets/reference/project-structure.md`

## Verify

```bash
npm run build
npm run dev
# browser-check the changed UI
```

## Security

- Treat any API keys in the client as public; never put server secrets in Vite env prefixed for the browser
- If you add a backend later, validate there — not only in the UI
- MCP: `context7`; `playwright` or Chrome DevTools for UI verification

## After scaffold

- Keep a real `npm run dev` script. Do not ship a lone HTML file.
- Write run/test steps into `AGENTS.md`.
