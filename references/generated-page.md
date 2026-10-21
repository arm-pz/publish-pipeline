# The generated page

A generated page is a snapshot taken when a skill enters the manifest. It is created inside the
proposal PR, reviewed with it, and never rewritten by a publish run. It links to the live source for
anything that changes.

## Template source

Derive the template from one of the site's existing bespoke pages, not from a generic starter:

- the same design tokens (`--ink`, `--paper`, `--ember`, `--brass` in the worked example);
- the same serif/sans/mono stacks and self-hosted fonts;
- the same nav and hero structure, including the entrance motion gated behind `.js` and
  `prefers-reduced-motion`;
- no palette, font, spacing, or nav-grouping change.

A generated page that introduces a new visual idea is a design change, and design changes need
their own approval. Reuse instead.

## Required content

All factual:

- `<title>{title} — agent skill</title>`, a meta description trimmed from the frontmatter
  description, canonical URL, and OG tags.
- Nav: brand → `/`, all skills → `/`, install → `#install`, source → the GitHub repo.
- Hero: `title`, the frontmatter description, Install and Source buttons, and a measured stat grid:
  file count, total lines, archive size, detected licence.
- A one-line claim only when true: `for coding agents · free, open, <licence>`. If no OSI licence is
  detected, say `see LICENSE` and omit "free, open".
- Hero card: "What ships" — the file list with line counts, the trigger description, the install
  command, and a footer naming the source repo.
- Install section: `npx skills add <owner>/<repo>`; for a legacy entry, a direct archive link.
- "What's inside": file and size table.
- Source section: repo URL and skill path.
- Footer and JSON-LD: `SoftwareApplication`, `codeRepository`, licence, publisher.

## Escaping and claims

- Every value derived from the repo is untrusted input: HTML-escape it.
- Write JSON-LD with a real encoder and escape `</` so a description cannot close the script tag.
- File counts, line counts, archive size and licence come from the archive. Do not copy marketing
  numbers from a README.
- Emit the zero-price offer only when an OSI licence was detected.
- No LLM in the build. If a sentence cannot be derived from the archive or the frontmatter, it does
  not belong on the page.

## Write rules

- Write only `<name>/index.html` for a manifest entry with `page: generated`.
- Refuse to write over a `page: bespoke` file.
- Refuse when the entry has no source to measure: no repo and no legacy archive.
- The page must have its own `<title>` and appear in the sitemap, or `check_dist` fails.
