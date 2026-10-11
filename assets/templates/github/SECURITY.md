# Copy to SECURITY.md at the repo root (or docs/SECURITY.md).

# Security policy

## Supported versions

Document which branches or releases receive fixes.

| Version | Supported |
| --- | --- |
| main | yes |
| older tags | no |

## Reporting a vulnerability

Do **not** open a public issue for security reports.

- Email: security@example.com (replace)
- Or use GitHub Private Vulnerability Reporting if enabled

Include: impact, steps to reproduce, affected versions, and whether a fix is known.

We aim to acknowledge within 5 business days. Please give us a reasonable window before public disclosure.

## Secrets

Never commit API keys, tokens, or private keys. Use `.env` locally and platform secret stores in CI/Cloud.
