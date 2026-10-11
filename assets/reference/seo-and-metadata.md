# SEO and metadata

Public pages need shareable identity. Internal tools can skip most of this.

## Basics

- Unique `<title>` and meta description per important route
- Canonical URL when the same content has multiple URLs
- Favicon + app icons (at least one working favicon in the browser tab)

## Sharing

- Open Graph: `og:title`, `og:description`, `og:image`, `og:url`
- Twitter/X card tags when you care about that preview
- Absolute HTTPS URLs for images

## Crawling

- `robots.txt` intentional (do not accidentally block everything in prod)
- Sitemap when there are many public URLs
- Auth-only apps: mark private routes `noindex` when appropriate

## Verify

- View source / browser tab title
- OG debugger or a share preview tool for the production URL after deploy

## See also

- `assets/checklists/ui-polish.md`
