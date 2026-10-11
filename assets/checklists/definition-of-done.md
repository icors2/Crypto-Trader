# Definition of done

Do not claim a change is done until the applicable boxes are checked.

## Always

- [ ] Behavior matches the request (or documented intentional scope cut)
- [ ] `verify-change` ran; commands and results are stated
- [ ] **Smoke check** of the critical path ran (not only compile/typecheck)
- [ ] No secrets introduced (`.env` untracked; `${env:NAME}` for MCP)
- [ ] Working memory updated if a durable fact/decision/lesson changed
- [ ] Lint/typecheck clean for touched languages (or N/A)

## When code changed

- [ ] Tests added or updated for non-trivial logic (preferred; smoke still required)
- [ ] Build succeeds if deploy/bundle is affected
- [ ] User-visible UI checked in a browser (or explicitly deferred)

## When security-sensitive

Auth, payments, secrets, PII, public APIs, file uploads, webhooks:

- [ ] `security-review` (or `security-reviewer` subagent) ran
- [ ] Critical/High findings fixed or accepted by the user in writing

## When shipping

- [ ] `ship-change` followed (branch, conventional commit, PR if applicable)
- [ ] CI green or failures explained

## Starter / Cursor setup edits

- [ ] `npm run verify` passes (audit + secret scan)
- [ ] Skill `name` matches folder; rules are `.mdc`
