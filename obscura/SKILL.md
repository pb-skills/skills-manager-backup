---
name: obscura
description: Fetch, render, and scrape specific web pages with the Obscura headless-browser CLI instead of the built-in web fetch tool. Use whenever the task is to load a URL and read or extract its content (page text, Markdown, rendered HTML, links, JS-rendered data, screenshots, PDFs) — Obscura runs real JavaScript via V8, renders natively, and uses ~30 MB memory versus 200+ MB for headless Chrome.
---

# Obscura

Fetch web content through [Obscura](https://github.com/h4ckf0r0day/obscura) — the headless-browser CLI — instead of the built-in `web_fetch` tool. Obscura runs real JavaScript via V8 and renders pages natively, so it returns what a real browser sees, with ~30 MB memory and ~85 ms page loads. It is already installed on this system at `C:\Apps\obscura.exe` and is on `PATH` (verify with `obscura --version`).

## When to use

Use Obscura whenever the task is to **load a specific URL** and read or extract its content:

- Reading or summarizing a web page.
- Extracting structured data, links, headings, or rendered text.
- Fetching a page that needs JavaScript to render (SPAs, XHR-driven content).
- Capturing a screenshot or exporting a PDF of a page.
- Fetching a resource that the built-in fetcher returned empty, blocked, or without JavaScript.

Obscura is a fetch/load tool, **not a search engine**. To discover which URLs exist, use `web_search` first, then hand the chosen URL to Obscura. Fall back to `web_fetch` only when Obscura is missing or a fetch still fails after the remedies below — and say so.

## Core commands

The primary command is `obscura fetch`. Always pass `--quiet` to suppress the progress banner, and a bounded `--timeout` (seconds).

### Read a page as Markdown (default)

```bash
obscura fetch <url> --dump markdown --quiet --timeout 20
```

`--dump` choices, by what you need:

| `--dump`      | Returns                                                        |
|---------------|----------------------------------------------------------------|
| `markdown`    | DOM converted to Markdown — best for reading and for the model |
| `text`        | Readable body text                                             |
| `html`        | Rendered HTML after JavaScript executes                        |
| `links`       | All `<a href>` URLs on the page                                |
| `original`    | Raw response body, binary-safe (images, JSON, JS, CSS)         |
| `assets`      | NDJSON of every sub-resource URL the page references           |

### Extract a specific value with JavaScript

```bash
obscura fetch <url> --eval "document.title" --quiet
obscura fetch <url> --eval "Array.from(document.querySelectorAll('a')).map(a=>a.href).join('\n')" --quiet
```

### Dynamic content / waiting

```bash
# Wait for the network to go quiet (500 ms window) before dumping
obscura fetch <url> --dump markdown --wait-until networkidle0 --quiet

# Wait for a CSS selector to appear
obscura fetch <url> --dump markdown --selector "#app.loaded" --quiet

# Longer navigation budget for slow SPAs
obscura fetch <url> --dump markdown --timeout 45 --quiet
```

### Screenshot / PDF

```bash
obscura fetch <url> --screenshot page.png --quiet     # or: -s page.png
```

Then inspect the image with the image reader. Rendering is included in the release binary.

### Write output to a file instead of stdout

```bash
obscura fetch <url> --dump markdown --output page.md --quiet
```

### Fetch a non-HTML resource verbatim

```bash
obscura fetch <url> --dump original > asset.bin
```

## Batch / parallel (the queue)

For several URLs at once use `scrape` — it runs them in parallel with worker processes and returns results in input order:

```bash
obscura scrape <url1> <url2> <url3> --concurrency 10 --eval "document.title" --format json --quiet
```

## Options that matter

| Flag | Purpose |
|------|---------|
| `--stealth` | Anti-fingerprinting + tracker blocking (3,520 domains). Use for anti-bot / Cloudflare-protected sites. |
| `--proxy <url>` | Route through an HTTP/SOCKS5 proxy. |
| `--user-agent <ua>` | Override the User-Agent. |
| `--v8-flags "<flags>"` | Raise the V8 heap for JS-heavy pages, e.g. `--v8-flags "--max-old-space-size=4096"`. |
| `--allow-private-network` | Permit localhost/LAN fetches (blocked by default for SSRF protection). |

## Windows invocation notes

The binary is `C:\Apps\obscura.exe` and on `PATH`. Two gotchas:

1. **Always pass `--quiet`.** Without it Obscura writes `Fetching…` and `Page loaded…` to stderr, which PowerShell surfaces as `NativeCommandError` and can look like a failure even when the fetch succeeded.
2. **Check the real exit code.** In PowerShell, discard stderr and read `$LASTEXITCODE`:

```powershell
& obscura fetch <url> --dump markdown --quiet 2>$null
Write-Output "EXIT=$LASTEXITCODE"
```

In bash the banner simply goes to stderr; `--quiet` removes it.

## Troubleshooting

- **Not found / command fails**: run `obscura --version` (expect `obscura 0.2.6` or later). If absent, fall back to `web_fetch` and report that Obscura is missing.
- **`JavaScript heap out of memory`**: add `--v8-flags "--max-old-space-size=4096"`.
- **Private/LAN URL blocked**: add `--allow-private-network` (loopback/RFC1918 are blocked by default as SSRF protection).
- **Hangs on a heavy SPA**: raise `--timeout`, and add `--wait-until networkidle0` or `--selector`.
- **Empty result**: try `--dump html` to see whether content is JS-rendered, then add `--wait-until networkidle0`.

## Guardrails

- Obscura loads specific URLs; it is not a search engine. Use `web_search` to find URLs, then Obscura to load them.
- Never use it against private/internal targets unless the user explicitly asked, and then add `--allow-private-network`.
- Use `--stealth` for anti-bot but do not bypass paywalls or access controls the user is not authorized to use.
- Prefer `--dump markdown` for model consumption to keep context small; use `--dump original` only for binary resources.

## Advanced (optional)

For interactive automation — clicking, typing, multi-step flows — Obscura also ships an MCP server (`obscura mcp`) and a Chrome DevTools Protocol endpoint (`obscura serve --port 9222`) that Puppeteer/Playwright can drive. Use those only when the task needs interaction beyond loading a page; plain `obscura fetch` covers every "fetch something from the internet" case.
