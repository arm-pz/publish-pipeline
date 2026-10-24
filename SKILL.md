---
name: publish-pipeline
description: >-
  Sets up, audits and repairs a manifest-driven CI/CD pipeline that publishes a
  collection of agent skills to a Cloudflare Pages site, with a generated page
  per skill. Use when someone asks for CI/CD or automation for a skills site,
  wants a new skill repo to appear on the site with its own page, asks why a
  skill is missing or its page is stale, or needs a red publish run diagnosed
  and a bad deploy rolled back. It installs one GitHub Actions workflow with
  check and publish jobs, a review-PR or auto-sync publication gate, generated
  hub rows, discovery indexes, sitemap and pages, and gates on both sides of
  the deploy. Not for releasing one skill
  through the marketplace, tarball or plugin channels (use
  publish-release-gate), checking unpushed work or listing drift (use
  upstream-check), deciding whether a build is safe to launch (use
  release-gate-chair), or writing and tuning a skill (use draft-skill or
  tune-skill).
---

# Publish pipeline

Owns the machine that turns skill repos into a published site: the manifest, the workflow, the
generators, the gates, and the recovery path. It does not own one skill's release through the
marketplace or tarball channels (`publish-release-gate`), or page copy and visibility audits
(`findable`).

The rule the whole design rests on: **the owner chooses the publication gate, once, in writing.**
There are two, and `references/design.md` records which one a site runs:

- **review** (the default): a pushed skill is not a published skill. Discovery opens a pull request;
  a human merges it; that merge is the publication decision and the deploy trigger.
- **auto**: a public repo that passes the shape test is the publication decision. An hourly sync
  adds it, refreshes generated pages whose repo moved, follows renames with 301 redirects and drops
  repos that went away; every gate still has to pass before the deploy, and the sync is committed
  back only after the live proof.

Never switch a site between them on your own judgement, and never mix them in one workflow.

Worked example: `arm-pz/skills-site` → Cloudflare Pages project `skills` →
`https://skills.caffeinity.com`. The reasons behind the design are in `references/design.md`. The
machine was implemented there on 2026-10-21; its pull-request check job has run green, while the
publish, rollback and discovery proofs have not. Report evidence you produced, not steps you
believe would work.

## 0. Audit the live site before changing anything

Measure what exists today. Do not seed the manifest from a README, a memory, or a count someone
quoted.

```
gh api repos/<owner>/<repo>/contents/.github/workflows --jq '.[].name'   # empty means no CI
npx wrangler pages project list                                          # Direct Upload vs Git
curl -s https://<site>/ | grep -o 'class="skill"' | wc -l               # the site's card selector
curl -s https://<site>/agent-skills/index.json | python -c 'import json,sys; print(len(json.load(sys.stdin)))'
curl -s https://<site>/.well-known/agent-skills/index.json | python -c 'import json,sys; print(len(json.load(sys.stdin)))'
curl -s https://<site>/sitemap.xml | grep -c '<url>'
```

Record four numbers and their source: cards on the hub, entries in each discovery index, sitemap
URLs, and pages that exist. Every difference between them must be explainable as a `page: none`
entry or a defect. Seed from the live state, then list every known drift in the PR body — do not
silently pick one surface as truth.

A bare `200` is not proof a page exists; Cloudflare Pages can answer unknown paths with the hub
or another fallback. Compare a real `<title>` or content hash. See `references/gotchas.md`.

## 1. Write the manifest

`site/skills.json` decides what is public. `site/deny.json` vetoes repos before discovery proposes
them. Schema, page kinds, group and tag rules, legacy entries and the seeding procedure are in
`references/manifest.md`.

Gate: run the validator on every edit.

```
python scripts/validate_manifest.py site/skills.json site/deny.json
```

## 2. Make the generators reproduce today first

Before any generator replaces a hand-edited surface, prove it can reproduce the current one from
the seeded manifest:

- hub rows and JSON-LD, inside marked regions only;
- both discovery indexes, written from one byte string;
- sitemap, with per-path dates from `git log` (needs full history);
- the page template, derived from an existing bespoke page (contract in
  `references/generated-page.md`).

Gate: regenerate into a scratch directory and diff against the live baseline. A diff is either
explained and approved, or the manifest or generator is wrong. Do not deploy on the first run that
"looks right"; this step is the regression test the rest of the pipeline stands on.

Newline discipline matters here: preserve each served file's line endings and write JSON/XML as LF.
Measure per file rather than assuming — in the worked example `index.html` is LF while some bespoke
pages are CRLF. The first CI run should not rewrite every line.

## 3. Build the gates before the deploy

The gate order is fixed:

```
tests → build → generated-surface check → make_dist → check_dist → verify local
      → secrets preflight → deploy → verify live with cache-buster → prove live
```

`references/verification.md` lists what each gate must assert. Three rules apply everywhere:

- A red gate blocks every entry, not just the bad one. One broken skill does not half-publish.
- The publish job has no repository write permission. Secrets reach only the deploy step and are
  never printed.
- A build that is missing a manifest entry fails; it does not silently publish fewer skills.

## 4. Write one workflow with three jobs

Triggers:

- `push` to `main` → publish;
- `schedule` (daily) → publish and discover as independent jobs;
- `workflow_dispatch` with `mode: publish | discover` → the selected job;
- `pull_request` → check only, no deploy and no Cloudflare secret.

Do not add `repository_dispatch`, and do not add a dispatcher workflow to each skill repo. On a
user account there are no org secrets or org webhooks; every repo that dispatches needs its own
PAT. A scheduled poll from the site repo is the zero-touch trigger.

Permissions: top-level `contents: read`; `discover` alone gets `contents: write` and
`pull-requests: write`; `publish` gets no write. Separate concurrency groups for publish and
discover, neither cancelling in progress. The full job graph, permissions and a YAML skeleton are
in `references/workflow.md`.

`GITHUB_TOKEN`-opened pull requests do not trigger `pull_request` workflows. The discovery job must
run the check itself before opening the PR. The repository must also allow Actions to create pull
requests.

## 5. Make discovery propose, or sync in auto mode

The shape test decides eligibility; the manifest decides publication. The eight clauses, the
explicit-path test and the proposal workflow are in `references/shape-test.md`. The load-bearing
one: exactly one `SKILL.md`, at exactly one of `SKILL.md`, `<repo-name>/SKILL.md`, or
`skills/<repo-name>/SKILL.md`. Test the three paths explicitly, not with a regex.

A proposal PR contains: the manifest entry, the generated page, the regenerated hub, the archive
digest, measured stats, the install command, the auto-assigned group and tag, and a checklist for
the reviewer. Run the full local gate before pushing; if it fails, open no PR and report why.
Never deploy from the discover job and never give it a Cloudflare secret.

In **auto** mode there is no proposal: `sync.py --write` runs at the start of the publish job and
applies five actions: add, refresh, rename, remove, hold. Rules that keep it safe:

- An unreadable repo stops the run; only an explicit Not Found (or a repo that turned private)
  removes an entry.
- A rename keeps the hand-written copy, moves the page folder, records the old name as an alias,
  and `_redirects` sends the old page and archive URLs to the new ones. A bespoke page is moved,
  never edited; the run reports that its copy may still use the old name.
- An empty About or a failed shape test is held and reported, never published with a guess.
- Deploy only when `dist/version.json` (a hash over the built tree) differs from the live one, so
  an hourly schedule does not redeploy an unchanged site.

## 6. Untrack build outputs only after CI reproduces them

Build outputs — `dist/`, packed archives (not the pinned legacy archives), both discovery indexes,
`sitemap.xml` — should stop being committed, but the order matters:

1. Run the new pipeline on a branch while the old artifact tree is still tracked.
2. Compare the built file set and hashes against what production currently serves.
3. Explain every difference; fix the build until the match is clean.
4. Only then remove the tracked outputs and add them to `.gitignore`.

A Pages deploy replaces the whole artifact set. A build that forgets `404.html` does not produce a
404 — it makes every path answer 200 with the fallback page. Keep the full set: pages, indexes,
sitemap, `_headers`, `404.html`, and any `.well-known` roster.

## 7. Hand the human steps back

Do not perform these silently, and never write a secret into a file, a log, or a commit:

- Decide where deploys run, and record it in `references/design.md`. Either CI deploys, and the
  owner pastes `CLOUDFLARE_API_TOKEN` (Pages Read + Edit, scoped to the one project) and
  `CLOUDFLARE_ACCOUNT_ID` into the repo's Actions secrets (`gh secret set` is reported broken on
  this machine; give the exact Settings → Secrets path), or CI holds no Cloudflare credentials and
  the owner deploys from their own machine with `deploy.sh` and `npx wrangler login`. Never put a
  token in the repo to make either work.
- Enable "Allow GitHub Actions to create and approve pull requests".
- Optionally require the `check` job on `main`.
- Approve the first publish and the rollback drill.

## 8. Prove it before calling it done

Three proofs, each with pasted evidence:

1. **Publish:** a manual run deploys, the deployment URL is recorded, and the live discovery index
   is byte-identical to the built one when fetched with a cache-buster.
2. **Rollback:** activate the previous Pages deployment, confirm the old content is served, then
   reactivate the new one. Record the deployment IDs.
3. **Discovery:** a new skill repo produces exactly one proposal PR; its checks pass; merging it
   deploys; the live hub, both indexes, sitemap and page include it; no other skill's copy changed.

Until all three have run in the target repo, describe the pipeline as unproven.

## Operating it

- **Add a skill by hand:** edit the manifest, validate it, generate, run the local gates, open a
  PR, merge. Do not hand-edit a generated page or one of the two indexes.
- **Review a proposal:** check the group, tag, blurb, stats and digest against the repo; correct
  the copy in the PR; merge only after the checks are green.
- **A page is stale:** generated pages are snapshots by design. Refresh means regenerating that page
  in a PR, not editing it in `dist/`. The discovery entry and archive still refresh on publish.
- **A deploy is bad:** roll back in the Pages dashboard to the previous deployment, then fix the
  cause in git. Never patch production by hand.
- **One skill needs releasing now:** hand `publish-release-gate` the skill path and repo name for
  the marketplace entry. Its manual tarball and discovery-index steps are superseded once this
  pipeline exists; never run both paths against the same site.
- **Live differs from built:** say "deployed but live verification failed (cache or propagation)",
  not "deploy failed". Re-fetch with a cache-buster before deciding; roll back only if it persists.

## Stop rules

- An empty repo About is a build failure, not a fallback to the last description.
- A legacy archive whose sha256 does not match is a build failure.
- Two surfaces that must agree are never patched into agreement; fix the input and regenerate both.
- Never overwrite a `page: bespoke` file. In review mode, never create a page outside a reviewed
  PR; in auto mode, only the sync creates pages, and only inside a run whose gates all passed.
- Never publish a repo in `site/deny.json`, and never remove a denial without the user's decision.

## References

When a rule here and a reference disagree, this file wins; references carry the detail.

- `references/manifest.md` — schema, page kinds, group/tag rules, legacy archives, seeding.
- `references/generated-page.md` — the page template, content contract, escaping and measured claims.
- `references/shape-test.md` — eligibility clauses, explicit paths, proposal behaviour, auto-assignment.
- `references/workflow.md` — triggers, permissions, job steps, YAML skeleton.
- `references/verification.md` — every gate's assertions, live proof, failure language, rollback drill.
- `references/gotchas.md` — platform and CI behaviour that silently breaks this pipeline.
- `references/design.md` — the decisions and rejected alternatives, when someone challenges a rule.
- `scripts/validate_manifest.py` — the manifest gate; run it on every edit.
