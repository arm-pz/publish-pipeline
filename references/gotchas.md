# Gotchas

Behaviour that silently produces a green-looking, wrong result.

## Pages

- **A deploy replaces the whole artifact set.** Uploading a build that lacks a page deletes that
  page from production. There is no merge. This is why `check_dist` asserts the full set.
- **A missing `404.html` makes every unknown path return 200.** Pages falls back to the site's
  index, so `/anything/` answers with the hub. A `200` is not proof a file exists; compare a real
  `<title>` or content hash.
- **Direct Upload projects ignore git.** A push does nothing until a deploy call uploads a new
  artifact set. Confirm the project type with `wrangler pages project list` before assuming a git
  integration exists.
- **The deployment history is the rollback mechanism.** Previous deployments stay available;
  rollback is a pointer change in the dashboard.
- **Email obfuscation rewrites served HTML.** Cloudflare replaces literal email addresses with a
  `/cdn-cgi/l/email-protection` link, so a byte-diff against source on a page that mentions an email
  is expected.
- **Cache:** a deploy can take a moment to propagate. Re-fetch with a cache-buster before calling
  the deploy bad.

## GitHub Actions

- **PRs opened with `GITHUB_TOKEN` do not trigger `pull_request` workflows.** Run the checks inside
  the discover job before opening the PR. Human-opened PRs get the normal check.
- **Actions cannot open PRs by default.** Enable "Allow GitHub Actions to create and approve pull
  requests" in the repo settings.
- **`fetch-depth: 0` is required** for sitemap dates from `git log`, and for anything that reads
  history. The default shallow clone breaks it quietly.
- **Scheduled workflows run on the default branch only**, and GitHub disables them in public repos
  after 60 days without repository activity. Re-enable or dispatch manually.
- **Do not echo secrets in a preflight.** Test for emptiness and print only the variable name.
- **Pin wrangler.** A floating version can change upload or output behaviour with no commit.

## Worked-example machine quirks

- `gh` on PATH may be an unrelated npm package that crashes. Use the GitHub CLI by full path
  (`C:\Program Files\GitHub CLI\gh.exe`) or a shell alias.
- A Python subprocess that runs bare `bash` on Windows can resolve to the WSL stub, which fails with
  `execvpe(/bin/bash): No such file or directory` and a bare non-zero exit. Resolve Git's
  `bin/bash.exe` explicitly when a gate script shells out.
- `gh secret set` is reported broken here; hand the user the Settings → Secrets → Actions path
  instead of a command that will fail.
- `npx wrangler` can fail with `EBUSY` on the default npm cache. Use a clean cache:
  `npx --yes --cache /tmp/npxcache wrangler@latest <cmd>`.
- A cp1252 console mangles `→` and `—` on stdout into mojibake. Files written with
  `encoding="utf-8"` keep the correct bytes. Run Python with `-X utf8` for readable output, and pin
  served JSON/XML as `-text` in `.gitattributes` so checkout cannot rewrite their bytes.
- Line endings vary per served file: `index.html` is LF here, some bespoke pages are CRLF, and
  JSON/XML are LF. Compare normalized line endings before calling drift; preserve each served
  file's convention when generating.
- Two local clones of the same site repo can diverge. Deploy from one freshly built artifact tree,
  fetch and rebase before pushing, and check which commit production is serving with
  `wrangler pages deployment list --project-name <project>`.

## Content and manifest

- **Empty repo About:** fail the build. Falling back to a README line or the previous description
  publishes something nobody approved.
- **Descriptions are untrusted input.** HTML-escape every repo-derived value on a generated page,
  and write JSON-LD with a real encoder, escaping `</`.
- **Only measured numbers go on a page.** File count, line count, archive size and detected licence
  come from the archive. No "0 API keys" or similar claim unless the archive supports it.
- **"Free, open" needs a detected OSI licence.** Without one, link to `LICENSE` and say no more.
- **A generated page is a snapshot.** It does not refresh on publish. Refresh is a new PR.
- **Never overwrite `page: bespoke`.** The generator must refuse, not warn.
