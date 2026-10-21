# publish-pipeline

An agent skill for building and repairing the machine that turns skill repos into a published
site: one manifest, one workflow, generated pages, and gates that fail closed on both sides of the
deploy.

The rule the whole design rests on: **a pushed skill is not a published skill.** Discovery opens a
pull request for each eligible repo; a human merges it; that merge is the publication decision and
the deploy trigger. Anything that skips the pull request is a bug.

## Install

```
npx skills add arm-pz/publish-pipeline --skill publish-pipeline
```

Or copy the folder into `~/.qoder/skills/` (Qoder) or `~/.claude/skills/` (Claude Code), then start
a new session.

## Use it when

- A skills site needs CI/CD that gives every new skill repo its own page.
- A skill is on GitHub but missing from the site, or its page is stale.
- A publish workflow went red and needs the failing gate named before anything is edited.
- A deploy reported success and the live page is still the old one.

It is not the publisher for one skill through the marketplace, tarball or plugin channels (that is
`publish-release-gate`), not an unpushed-work or listing-drift audit (`upstream-check`), and not a
launch go/no-go (`release-gate`).

## What it sets up

| Piece | Responsibility |
|---|---|
| `site/skills.json` | The only place publication is decided. One entry per public skill. |
| `site/deny.json` | A durable veto list checked before discovery proposes anything. |
| `check` job | Every gate, no deploy and no Cloudflare secret, on pull requests. |
| `publish` job | Rebuilds, verifies, deploys, then checks what production actually serves. |
| `discover` job | Runs the shape test over public repos and opens one reviewed proposal PR. |

Gate order: unit tests, generated-surface checks, build, sitemap, `make_dist`, `check_dist`,
`verify.mjs local`, secrets preflight, deploy, live verify with a cache-buster, live proof.

A red gate blocks every entry. A build missing a manifest entry fails instead of publishing fewer
skills. A Pages deploy replaces the whole artifact set, so the build carries `404.html`, indexes,
sitemap and every page or the deploy is refused.

## What this repo carries

This skill is the contract, the decisions and the failure modes, plus the manifest validator:

- `SKILL.md` — the workflow.
- `references/manifest.md` — schema, page kinds, generated entries, legacy archives.
- `references/generated-page.md` — the page template and its measured claims.
- `references/shape-test.md` — eligibility clauses and proposal behaviour.
- `references/workflow.md` — triggers, permissions, job steps.
- `references/verification.md` — every gate's assertions, live proof, rollback.
- `references/gotchas.md` — platform behaviour that silently produces a wrong green.
- `references/design.md` — decisions and rejected alternatives.
- `scripts/validate_manifest.py` — run on every manifest edit.
- `tests/trigger-cases.md` — trigger and boundary cases, run by hand against the description.

The site's generators and CI scripts live in the target repository, not here. This skill tells you
what they must do and how to prove they do it.

## Status

Implemented in `arm-pz/skills-site` on 2026-10-21. The pull-request check job has run green there.
The publish, rollback and discovery proofs have not been run yet, so the pipeline is unproven until
those are recorded.

## License

MIT. See `LICENSE`.
