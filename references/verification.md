# Gates, live proof, rollback

Every gate fails closed. A red gate blocks every entry, not just the one that broke.

## Gate order

| Gate | What it proves | What a failure means |
|---|---|---|
| Unit tests | The tooling behaves as specified. | Fix the tool; do not deploy. |
| Build | Every manifest entry resolved, packed and digested. | A source is missing, an About is empty, or a legacy digest drifted. |
| Generated-surface check | The committed hub matches the manifest. | Someone hand-edited a generated region, or forgot to regenerate after a manifest edit. |
| `make_dist` | One artifact tree assembled from one run. | Copy logic or a missing input; inspect the tree, not the deploy. |
| `check_dist` | Every surface agrees with every other. | The build is internally inconsistent; the site must not ship. |
| `verify.mjs local` | Index entries match the archives' digests and frontmatter. | The archive and its published digest disagree. |
| Secrets preflight | Both Cloudflare values exist. | Human step missing; stop with a clear message, never echo the value. |
| Deploy | The artifact tree is uploaded. | Auth or network; retry after rotating or restoring secrets. |
| Live verify + proof | Production serves the bytes just built. | Deployed but live verification failed (cache or propagation) unless a cache-busted re-fetch still differs. |

## `check_dist` assertions

The local gate checks the assembled `dist/`, not the source:

- both discovery indexes exist, are byte-identical to each other, and match the built index;
- every index URL maps to an archive whose sha256 matches the index digest;
- every `page != none` entry has a page with its own `<title>`;
- every page appears in the sitemap;
- the hub has one card per page, and the JSON-LD item count equals the card count;
- `404.html`, `_headers`, and the `.well-known` roster exist;
- no path outside `dist/` is referenced;
- the archive count equals the number of manifest entries (no silent shrinkage).

## `verify.mjs` modes

- **local** reads the built index and maps each artifact URL to the archive beside it; it does not
  need the network.
- **live** fetches the discovery index from the site and checks each published artifact URL.
  Because those URLs are absolute, pointing live mode at a local server still checks the real
  domain. To validate an undeployed tree, hash each archive against its index entry directly.

Live mode should accept a `CACHE_BUST` value and append it to every request.

## Live proof

`prove.py` fetches the hub, each page, the sitemap, and both discovery indexes with a cache-buster
and asserts:

- the card count equals the manifest's page count;
- each page has a non-empty `<title>`; the title is not compared to `pageTitle`, so check the copy
  in the proposal PR;
- the sitemap URL set matches the pages;
- both discovery index bodies are byte-identical to the built bytes.

A mismatch here is reported as **"deployed but live verification failed (cache or propagation)"**,
not as a generic deploy failure. The deploy did happen; say so, then re-fetch before acting.

## Rollback

1. Open the Cloudflare dashboard → Pages → the project → Deployments.
2. Pick the last known-good deployment and roll back to it.
3. Re-fetch the hub, one page, and the discovery index with a cache-buster; compare against the
   expected bytes, not HTTP status.
4. Record both deployment IDs in the incident note.
5. Fix the cause in git and deploy forward; do not hand-edit production.

Deployments are immutable snapshots, so the previous one remains available. Rollback is a pointer
change, not a rebuild.

## First-run proof matrix

| Proof | Evidence to paste |
|---|---|
| Publish | Deployment URL; live index sha256 equals the built index sha256 |
| Rollback | Old deployment ID active; old content served; new deployment restored |
| Discovery | Proposal PR URL; checks green; merged; live hub, indexes, sitemap and page include the skill; diff shows no other skill changed |

Until this matrix is filled in the target repository, the pipeline is unproven. Say that plainly in
the handover.
