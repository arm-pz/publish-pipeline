# The workflow

One workflow file, three jobs. The job that can write is never the job that deploys.

## Triggers

| Event | Job(s) | Why |
|---|---|---|
| `push` to `main` | publish | A merged proposal or a manifest edit deploys immediately. |
| `schedule` (daily) | publish and discover, independently | Catches skill-source updates and backfills; discovery finds new repos. |
| `workflow_dispatch` with `mode` | the selected job | Manual escape hatch; `publish` is the default. |
| `pull_request` | check | Build and verify without a deploy or a Cloudflare secret. |

No `repository_dispatch` and no per-repo dispatcher workflows. On a user account there are no org
secrets or org webhooks, so every dispatching repo would carry its own PAT. A poll from the site
repo is the zero-touch alternative.

## Permissions and concurrency

| Scope | Permission | Note |
|---|---|---|
| Top level | `contents: read` | Everything inherits this unless a job overrides it. |
| `check` | `contents: read` | No secrets. |
| `publish` | `contents: read` | Cloudflare secrets are passed to the deploy steps only. |
| `discover` | `contents: write`, `pull-requests: write` | Only runs on schedule or manual dispatch. |

- `publish` concurrency group `publish-<site>`, `cancel-in-progress: false`.
- `discover` concurrency group `discover-<site>`, `cancel-in-progress: false`.
- `check` concurrency per PR ref.

Two deploys racing would each upload a complete artifact set; serialising publish removes the
question of which one won.

## Publish steps

1. Checkout with `fetch-depth: 0` — the sitemap takes per-path dates from `git log`.
2. Python 3.11 and Node 24.
3. Unit tests for the tooling.
4. Manifest-driven build: fetch every repo-backed entry, pack deterministically, copy and verify
   legacy archives, write the archives and one index. Fail on a missing `SKILL.md`, an empty About,
   a legacy digest mismatch, or fewer entries than the manifest lists.
5. `gen_home.py --check` — the hub must already match the manifest. Publish never edits it.
6. `gen_sitemap.py --write` — output only, into the build directory.
7. Assemble `dist/`: static files, bespoke pages, generated pages, discovery indexes from one byte
   string, archives, sitemap. Keep `404.html`, `_headers`, and the `.well-known` roster.
8. `check_dist.py` and `verify.mjs local` — see `references/verification.md`.
9. Preflight both Cloudflare secrets without printing them.
10. Install the pinned wrangler version; deploy `dist/`.
11. Record the deployment URL in the job summary.
12. Verify live with a cache-buster, then run the live proof script.
13. Summary: skills attempted, each digest, the deployment URL, the live result.

## Discover steps

1. Checkout `main`, Python and Node.
2. `discover.py --report` — shape-test every public repo, write the table to the summary.
3. `discover.py --propose` — build, draft, generate, run the full local gate, commit to
   `proposal/<name>`, push, open the PR. Failures open no PR. See `references/shape-test.md`.

The discover job never deploys and never receives the Cloudflare secrets.

## Auto-mode publish steps

Only when `references/design.md` records the **auto** gate. The `discover` job is removed; the
publish job runs hourly (`17 * * * *`), on push to `main`, on manual dispatch and on
`repository_dispatch` type `skill-updated`, with `contents: write`:

1. `sync.py --write` — add, refresh, rename, remove or hold, then regenerate the hub and pages.
2. Unit tests, generated-surface checks, build, sitemap (also writes `out/_redirects`), dist (also
   writes `dist/version.json`), `check_dist.py`, `verify.mjs local`: the same gates as review mode.
3. Commit the sync to `main` as `github-actions[bot]` (`git pull --rebase` first). A push made with
   `GITHUB_TOKEN` does not start another run, so this cannot loop.
4. Compare `dist/version.json` with the live one. Never compare the live HTML: the CDN may inject
   markup into it. Then, by where `references/design.md` says deploys run:
   - **CI deploys:** deploy when they differ, then `verify.mjs` live and `prove.py`.
   - **Owner deploys** (arm-pz/skills-site since 2026-10-24): no Cloudflare credentials in CI.
     Keep one "Deploy pending" issue open while they differ and close it once they match; the
     owner runs `tools/agent-skills/deploy.sh` locally, which refuses anything but a clean, current
     `origin/main`, runs the same gates, deploys with their own wrangler login and proves the result.

The worked implementation is `arm-pz/skills-site` `.github/workflows/publish.yml`, plus a nightly
`health.yml` that runs tune-skill's `regress.py` over every published skill and opens an issue on a
regression.

## Check steps

Tests, build, `gen_home.py --check`, sitemap generation, `make_dist`, `check_dist`, and
`verify.mjs local`. No deploy, no secrets.

## Skeleton

This is the graph and the load-bearing lines, not a drop-in file. Script names come from the worked
example; replace the project name, site URL and paths.

```yaml
name: publish

on:
  push:
    branches: [main]
  schedule:
    - cron: "30 6 * * *"
  workflow_dispatch:
    inputs:
      mode:
        description: "publish or discover"
        type: choice
        options: [publish, discover]
        default: publish
  pull_request:

permissions:
  contents: read

jobs:
  check:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    concurrency:
      group: check-${{ github.event.pull_request.number }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: 24 }
      - run: python -m unittest discover -s tools/agent-skills/tests -v
      - run: python tools/agent-skills/build.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GH: gh
      - run: python tools/agent-skills/gen_home.py --check
      - run: python tools/agent-skills/gen_sitemap.py --write
      - run: bash tools/agent-skills/make_dist.sh
      - run: python tools/agent-skills/check_dist.py
      - run: node tools/agent-skills/verify.mjs local

  publish:
    if: >-
      github.event_name == 'push' ||
      github.event_name == 'schedule' ||
      (github.event_name == 'workflow_dispatch' && inputs.mode == 'publish')
    runs-on: ubuntu-latest
    concurrency:
      group: publish-skills-site
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: 24 }
      - run: python -m unittest discover -s tools/agent-skills/tests -v
      - run: python tools/agent-skills/build.py
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GH: gh
      - run: python tools/agent-skills/gen_home.py --check
      - run: python tools/agent-skills/gen_sitemap.py --write
      - run: bash tools/agent-skills/make_dist.sh
      - run: python tools/agent-skills/check_dist.py
      - run: node tools/agent-skills/verify.mjs local
      - name: Preflight Cloudflare secrets
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: |
          [ -n "$CLOUDFLARE_API_TOKEN" ] || { echo "::error::CLOUDFLARE_API_TOKEN missing"; exit 1; }
          [ -n "$CLOUDFLARE_ACCOUNT_ID" ] || { echo "::error::CLOUDFLARE_ACCOUNT_ID missing"; exit 1; }
      - run: npm install --no-save wrangler@4.151.1
      - name: Deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        run: npx wrangler pages deploy dist --project-name skills --branch main | tee deploy.log
      - run: grep -Eo 'https://[a-z0-9.-]+\.pages\.dev' deploy.log | tail -1 >> "$GITHUB_STEP_SUMMARY"
      - run: CACHE_BUST=${{ github.sha }} node tools/agent-skills/verify.mjs https://skills.caffeinity.com
      - run: python tools/agent-skills/prove.py --site https://skills.caffeinity.com --bust "${{ github.sha }}"

  discover:
    if: >-
      github.event_name == 'schedule' ||
      (github.event_name == 'workflow_dispatch' && inputs.mode == 'discover')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    concurrency:
      group: discover-skills-site
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - uses: actions/setup-node@v4
        with: { node-version: 24 }
      - run: python tools/agent-skills/discover.py --report
      - run: python tools/agent-skills/discover.py --propose
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Notes that bite

- `GITHUB_TOKEN`-opened pull requests do not trigger `pull_request` workflows. The discover job runs
  the same checks itself before opening the PR.
- The repo setting "Allow GitHub Actions to create and approve pull requests" must be on, or the
  PR step fails.
- `schedule` only runs on the default branch. GitHub disables scheduled workflows in public repos
  after 60 days without repository activity; re-enable them or use manual dispatch.
- Do not pass Cloudflare secrets at job level; keep them on the deploy and live-verify steps.
- Pin the wrangler version. A floating deploy tool changes behaviour without a commit.
