# Decisions and invariants

Written 2026-10-20 for `arm-pz/skills-site` → Cloudflare Pages project `skills` →
`https://skills.caffeinity.com`. The machine was implemented there on 2026-10-21; the pull-request
check job has run green, while publish, rollback and discovery proofs are still outstanding. When
someone challenges a rule in `SKILL.md`, this file holds the reason or the alternative that was
rejected.

## Decisions

| Question | Decision | Reason |
|---|---|---|
| Publication gate | A PR is opened for a new skill; merging it deploys. | Keeps public exposure and copy review in one place. The merge is the decision, recorded in git. |
| Per-skill page | Generated from a shared template for new skills; existing pages untouched. | A page per new skill has to work without hand design per repo. The template reuses the live design. |
| Discovery trigger | Scheduled poll plus manual dispatch from the site repo. | The owner is a user account: no org secrets or org webhooks. Cross-repo dispatch needs a PAT in every repo, including future ones. |
| Deploy trigger | Push to `main`, daily schedule, manual dispatch. | A merged proposal deploys immediately; the schedule catches source updates and backfills. |
| Build artifacts in git | Stop tracking `dist/`, packed archives, both discovery indexes and `sitemap.xml`. | They are derived. CI builds and verifies them every run, so drift and bot commits disappear. |
| Index descriptions | Repo About at build time for repo-backed entries; pinned for legacy entries. | The About is the agent-facing string. Fail loudly when it is empty. |
| Homepage copy | Hand-authored in the manifest, never derived from the About. | The site's voice is deliberately not the agent-facing description. |
| Group and tag for a discovered skill | Keyword heuristic, corrected by the reviewer in the PR. | Avoids a red placeholder PR while keeping categorisation reviewable. |
| Generated-page refresh | Not in v1. A generated page is a snapshot from when the skill entered the manifest. | Keeps the publish job read-only. The page links to the live source; the index still refreshes. |
| Existing page-less entries | Stay `page: none`; no backfill. | Avoids unrequested public changes to the current page set. |
| Per-repo dispatcher workflows | Not added. | They cannot authenticate to the site repo without a PAT. |
| Third-party skill `job-application-agent` | Denied by name in `site/deny.json`. | It fills and submits applications and transmits candidate data by default; it must not publish under this domain. |
| **2026-10-23: publication gate** | **auto** for `arm-pz/skills-site`, replacing the proposal PR. | The owner asked that anything with a SKILL.md live on the profile reach the site without a manual merge. The shape test, deny list and every build and live gate still apply. |
| 2026-10-23: discovery and deploy trigger | Hourly sync in the publish job; `repository_dispatch` (`skill-updated`) for an immediate run. | Hourly bounds the delay without a PAT in every repo; a repo that has a token can dispatch sooner. |
| 2026-10-23: generated-page refresh | On every sync when the repo HEAD moved; hand-written blurb, title and group are kept. | A page that shows a stale file list or commit is a wrong claim once publishing is automatic. |
| **2026-10-24: deploy location** | **The owner's machine** for `arm-pz/skills-site`: `deploy.sh` with their own `wrangler login`. CI keeps the sync and every gate, holds no Cloudflare credentials, and keeps a "Deploy pending" issue open while live is behind. | The owner does not want Cloudflare secrets in GitHub. The cost is that a merged change goes live when the owner deploys, not on its own. |
| 2026-10-23: renames | Follow the API redirect; alias plus `_redirects` 301s for the page and the archive. | findable can recommend a rename; the site must not 404 the old links or publish the skill twice. |

## Invariants

1. **Publication follows the recorded gate.** In review mode a push never publishes a new skill:
   discovery opens a PR and a human merges it. In auto mode the sync publishes, and only from a run
   whose build, gates and live proof all pass.
2. **Nothing deploys without a green build and verify.** A red verify blocks every entry.
3. **One manifest, many surfaces.** Hub rows, JSON-LD, both discovery indexes, sitemap and pages
   are generated from `site/skills.json` in one run. Files that must agree are written from one
   byte string, never edited twice.
4. **Hand-authored prose and bespoke pages are never rewritten.** Generators touch only marked
   regions and only `page: generated` files.
5. **A generated page is created only by the recorded gate.** Review mode: inside a reviewed PR.
   Auto mode: by the sync, committed to `main` after the live proof. Bespoke pages are never edited.
6. **A denied repo never publishes.** The deny list is durable and checked before any proposal.
7. **Deploy is atomic and reversible.** Each run creates a deployment; the previous one stays in
   history and can be reactivated. Rollback is a pointer change, not an edit under pressure.
8. **Every number on a generated page is measured.** No generated claim the archive cannot support.

## Rejected alternatives

- **Org-wide webhooks or repository dispatch.** Not available on a user account without a PAT per
  repo; a scheduled poll needs none.
- **Shape test alone as the publication rule.** It would publish every eligible repo at once,
  including pages nobody wrote copy for.
- **Hand-designing each new page.** Does not scale and reopens the design on every skill.
- **Letting discovery write directly to `main`.** Rejected for review mode, where it removes the
  gate. Accepted for auto mode on 2026-10-23 because the owner chose that gate; the bot commits only
  what it has already deployed and proved.
- **Refreshing generated pages during publish.** Makes the publish job a writer and its failures
  harder to reason about. Snapshot plus source link is enough for v1.
- **Publishing the two discovery indexes by hand.** They drifted apart in practice; one byte string
  written twice is the only reliable version.
- **Keeping build outputs tracked as a deploy safeguard.** Tracking was a workaround for gutted
  deploys. A CI gate that asserts the artifact set is stronger and does not store binaries in git.
- **Generating page copy with an LLM.** Unverifiable claims and unstable output. Copy is authored or
  derived from measured facts only.
