# The manifest

`site/skills.json` is the only place publication is decided. Discovery may propose an entry; only a
merged change to this file publishes one. `site/deny.json` is the durable veto list.

## Shape

```json
{
  "schema": 1,
  "site": "https://skills.caffeinity.com",
  "groups": [
    {
      "id": "writing-growth",
      "title": "Writing & Growth",
      "descriptor": "editorial · seo · discovery · chains",
      "order": 1
    }
  ],
  "skills": [
    {
      "name": "wordsmith",
      "repo": "arm-pz/wordsmith",
      "path": "skills/wordsmith",
      "group": "writing-growth",
      "tag": "editorial",
      "title": "Wordsmith",
      "blurb": "Teaches your agent to edit, not just generate: 44 commands across 5 disciplines that tighten, rewrite, critique and proofread while keeping the author's meaning, hedges and voice intact.",
      "stats": "44 commands · 5 disciplines · ~1,200 lines · 0 API keys",
      "install": "npx skills add arm-pz/wordsmith",
      "page": "bespoke",
      "order": 1
    },
    {
      "name": "new-skill",
      "repo": "arm-pz/new-skill",
      "path": "new-skill",
      "group": "skill-authoring",
      "tag": "authoring",
      "title": "New Skill",
      "blurb": "First sentence of the repo description, at most 240 characters.",
      "stats": "3 files · 210 lines · 4 KB",
      "install": "npx skills add arm-pz/new-skill",
      "page": "generated",
      "pageTitle": "New Skill — agent skill",
      "order": 30,
      "pageSource": {
        "description": "The repo About, normalized to one line when the proposal was drafted.",
        "files": [
          { "path": "SKILL.md", "lines": 180, "bytes": 3200 },
          { "path": "README.md", "lines": 20, "bytes": 900 },
          { "path": "LICENSE", "lines": 10, "bytes": 1100 }
        ],
        "fileCount": 3,
        "lines": 210,
        "bytes": 4096,
        "license": "MIT",
        "commit": "<40 lowercase hex characters>",
        "sha256": "<64 lowercase hex characters>"
      }
    },
    {
      "name": "release-gate",
      "repo": null,
      "path": null,
      "group": "ship-checks",
      "tag": "release",
      "title": "Release Gate",
      "page": "none",
      "order": 31,
      "legacy": {
        "archive": "release-gate.tar.gz",
        "sha256": "<64 lowercase hex characters>",
        "description": "Runs the three pre-launch passes in sequence and returns one release posture."
      }
    }
  ]
}
```

The group titles and descriptors are invented for the example; use the live site's own.

## Field rules

| Field | Rule |
|---|---|
| `name` | `^[a-z0-9]+(-[a-z0-9]+)*$`, max 64. It is the page path, the archive name, and the discovery entry name. |
| `repo` | `owner/name` whose basename equals `name`. `null` only for a legacy entry. |
| `path` | `"."` for a root-layout repo, `<name>` for a `<name>/SKILL.md` layout, `skills/<name>` for a plugin layout. `null` only when `repo` is null. |
| `group` | One of the `groups[].id` values. A skill cannot reference a missing group. |
| `tag` | One of the site's tag set. The worked example uses: `editorial`, `seo`, `discovery`, `career`, `learning`, `arena`, `decisions`, `authoring`, `release`, `performance`. |
| `title` | Human title for the card, page `<title>`, and JSON-LD. |
| `blurb` | Hand-authored homepage copy, stored verbatim. Required when `page` is not `none`. |
| `stats` | Hand-authored homepage stat line, stored verbatim. Required when `page` is not `none`. |
| `install` | Install command shown on the card and the page, stored verbatim. Optional; the generator falls back to `npx skills add <repo>`. |
| `page` | `bespoke`, `generated`, or `none`. |
| `pageTitle` | Generated pages only. The page `<title>`. Optional; falls back to `<title> — agent skill`. |
| `pageSource` | Generated pages only, required there and forbidden elsewhere. The measured facts below. |
| `order` | Integer, globally unique, fixes the sequence within a group. |

`blurb` and `stats` are never derived from the repo. The site's homepage voice is deliberately not a
copy of the agent-facing description. Descriptions for repo-backed entries come from the GitHub
repo About at build time instead.

## Page kinds

- **`bespoke`** — a hand-designed page exists at `<name>/index.html`. The generator may read it but
  must refuse to write over it. It appears on the hub and in the sitemap.
- **`generated`** — the generator owns `<name>/index.html`. It was created from the template inside a
  reviewed proposal PR and is a snapshot from the moment the skill entered the manifest. Refreshing
  it is a new PR that regenerates the page; it does not happen during a publish run.
- **`none`** — no page, no hub card, no sitemap URL. The discovery entry and the archive still
  publish, so agents can install the skill. Use this for legacy entries whose page was never written
  rather than backfilling a page nobody asked for.

## Generated entries

`page: generated` requires `pageSource`, the measured facts the page repeats. Discovery writes it
from the repo archive at proposal time; the reviewer corrects anything the measurements do not
support.

| Key | Rule |
|---|---|
| `description` | The repo About, normalized to one line. The page snapshot keeps it; the discovery entry still refreshes from the About on every publish. |
| `files` | Non-empty list of `{path, lines, bytes}` for the files the archive contains. |
| `fileCount` | Equals `len(files)`. |
| `lines` | Equals the sum of `files[].lines`. |
| `bytes` | The archive size. |
| `license` | SPDX id detected from the archive, or `NOASSERTION` when none is detected. |
| `commit` | 40 lowercase hex characters, the repo HEAD the archive was built from. |
| `sha256` | 64 lowercase hex characters, the digest of the archive the page describes. |

`pageTitle` is optional on a generated entry. Every value on the page is one of these measured
fields or hand-authored copy already in the entry; nothing is invented at render time.

## Group descriptors

Each group has a hand-authored `title` and `descriptor`. The generator writes
`{count} skills · {descriptor}` from the number of cards in the group, so adding a skill cannot
leave a stale count. Never store the count in the manifest.

## Descriptions for repo-backed entries

Fetched from the repo About at build time. Requirements: non-empty, normalized to one line, at most
1024 characters. An empty About is a build failure. Do not fall back to the README first paragraph
or the last published description; both hide the problem and publish something the repo owner did
not approve.

## Legacy entries

A legacy entry has no source repo, so it can never be rebuilt. It carries:

- `legacy.archive` — a committed filename resolved under `site/legacy/`. A path with a directory in
  it would be joined under that directory again and fail, so store the bare filename;
- `legacy.sha256` — 64 lowercase hex characters, verified against the archive on every build;
- `legacy.description` — the discovery description, pinned because there is no About to fetch.

A digest mismatch is a build failure. Never repack a legacy archive to "fix" it; that changes the
bytes agents already installed.

## Deny list

```json
[
  { "repo": "arm-pz/job-application-agent", "reason": "Third-party skill that submits applications and transmits candidate data by default." }
]
```

- Discovery checks this before it shape-tests a repo, and skips denied repos silently in reports,
  loudly in the summary.
- A denial is durable. Removing one is the user's decision, recorded in a PR with the reason.
- Deny a repo by name, not by topic or description: a reworded About must not defeat the veto.

## Seeding

The first manifest is migrated from the live site, not retyped:

1. Take names, repos and digests from one discovery index.
2. Take card positions, tags, blurbs and stats from the hub.
3. Take group ids, titles and descriptors from the hub headings.
4. Take skill paths from the build script, plus any root-layout repos it omits.
5. Classify every entry as `bespoke` (page exists), `generated` (new page required), or `none`.
6. Pin the repo-less entries as legacy archives with their current digests.
7. Write `deny.json` with the known vetoed repo and its reason.

The seeding script is a one-time migration. It is removed once the seeded manifest is committed and
the generators reproduce the live surfaces; the committed manifest, not the script, is the source
from then on. Never reintroduce it as a recurring build step, and never run one against a manifest
a human has already edited.

Validate every edit:

```
python scripts/validate_manifest.py site/skills.json site/deny.json
```
