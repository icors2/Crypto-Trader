# Recipe: File upload

**Sensitive:** yes — validate type/size; no public write buckets without auth.

## Goal

Authenticated (or explicitly public) user uploads a file; app stores it and can display or download it safely.

## Defaults (if unset)

- Object storage: S3-compatible, Cloudflare R2, Supabase Storage, Vercel Blob, or Netlify Blobs for assets.
- Prefer **signed upload URLs** or server-mediated upload over trusting raw multipart to a wide-open bucket.

## Minimum slice

1. Env names for storage credentials / bucket.
2. Server validates: content type allowlist, max size, authz.
3. One upload path + one display/download path.
4. Stored object key is not a raw user-controlled path (generate IDs).

Out of scope for v1: image CDN transforms (unless required), virus scanning, multi-GB uploads.

## Security

- Never trust `Content-Type` alone for executables; allowlist extensions/MIME and prefer magic-byte checks when available.
- Private by default; signed read URLs with expiry for private objects.
- Authz: user can only access their objects (or role-permitted).
- See `assets/checklists/security-review.md` uploads section.

## Verify

- Upload works; oversize / bad type rejected
- Unauthorized user cannot read private object
- `security-review`

## MCP

Vendor MCP only if managing buckets via tools this session.
