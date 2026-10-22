# Shape test and discovery proposals

The shape test answers "is this repo a standalone skill we could publish?" The manifest answers
"do we publish it?" Discovery runs the first and proposes; only a human merge answers the second.

## The eight clauses

A public repo is eligible only when every clause holds.

1. **Exactly one `SKILL.md`** in the tree, at exactly one of these paths:
   - `SKILL.md` (root layout),
   - `<repo-name>/SKILL.md`,
   - `skills/<repo-name>/SKILL.md`.

   Test the three explicit paths. Two or more `SKILL.md` files, or one at another depth, fails. A
   regex like `[\w./-]+SKILL\.md` cannot match a bare root `SKILL.md` and will silently reject
   valid root-layout repos; do not reintroduce one.

2. **`LICENSE`** at the repo root.
3. **`README.md`** at the repo root.
4. **`.claude-plugin/plugin.json`** at the root parses as JSON. Its `skills` key is **optional**:
   root-layout and `<repo>/`-layout repos commonly omit it. If present, it is a string or an array
   of strings, and every path resolves in the tree to the directory containing the single
   `SKILL.md`. Absence is allowed; a present but broken key fails.
5. **Frontmatter `name`** equals the `SKILL.md` folder name (for a root `SKILL.md`, the repo name)
   and equals the repo name.
6. **Frontmatter `description`** is present, single-line after whitespace normalization, and at most
   1024 characters.
7. **Not a fork.**
8. **Not in `site/deny.json`.**

Clauses 1 and 4 are where naive implementations go wrong. Both are explicit path/shape tests, not
pattern guesses.

## Report mode

`discover --report` fetches every public repo of the owner (`gh repo list --limit 1000`, which
returns forks too) and prints a table:

| repo | eligible | clauses failed |
|---|---|---|

Forks are listed and fail clause 7; they are not dropped from the report. Write the same table into
the job summary. Report mode never edits the manifest, a branch, or a PR.

`--only name[,name]` scopes a run to named repos and errors on a name it cannot find among the
owner's public repos. Use it when one skill must be proved through the pipeline without proposing
every other eligible repo in the same PR. CI runs without it, so a scheduled run still proposes the
full eligible set.

## Proposal mode

`discover --propose` is the only mode that writes. Skip, before doing any work:

- names already in the manifest;
- repos in `deny.json`;
- forks;
- any open pull request whose branch starts with `proposal/`. One run proposes every eligible repo
  on a single `proposal/<YYYY-MM-DD>` branch rather than one branch per skill.

For each eligible repo:

1. Build the deterministic archive and compute its digest.
2. Derive `path` from where the single `SKILL.md` lives.
3. Measure stats from the archive, never from marketing copy.
4. Draft `title`, `blurb`, `stats`, `group` and `tag` with the heuristics below.
5. Set `page: generated`, add the manifest entry, generate `<name>/index.html`, and regenerate the
   hub rows and JSON-LD.
6. Run the full local gate — tests, build, `check_dist`, `verify.mjs local`.
7. Commit to `proposal/<name>`, push, and open a PR.

If step 6 fails, open no PR. Report the failing gate in the job summary.

The PR body lists: the shape clauses passed, the archive digest, the measured stats, the install
command, the auto-assigned group and tag, and a checklist for the reviewer. The generated page is
part of the PR, so the page is reviewed before it ever reaches `main`.

## Auto-assignment heuristics

These are guesses a reviewer corrects in the PR, not policy.

| Group | Keywords in name or description |
|---|---|
| `career` | resume, CV, LinkedIn, recruiter, applicant, job, interview, career |
| `writing-growth` | seo, keyword, search, content, copy, edit, write, wordsmith, discover, findable, listing |
| `thinking-learning` | teach, learn, study, tutor, explain, decision, debate, brainstorm, crash, arena |
| `ship-checks` | release, ship, deploy, security, red-team, preflight, audit, performance, test, verify |
| `skill-authoring` | none — it is the fallback when no other group matches |

Tag follows the group:

- `career` → `career`
- `writing-growth` → `seo` for seo/keyword, `discovery` for discover/findable/listing, else
  `editorial`
- `thinking-learning` → `learning`, `decisions`, or `arena`
- `ship-checks` → `performance` for performance, else `release`
- `skill-authoring` → `authoring`

Other drafted fields:

- `title` — repo name split on hyphens, title-cased.
- `blurb` — first sentence of the description, at most 240 characters, ellipsis if cut.
- `stats` — `{files} files · {lines} lines · {kb} KB`.

All five are editable in the PR. The reviewer owns the final copy.

## Reviewer checklist

- Does the group match what the skill actually does, not just one keyword?
- Does the tag match the site's existing tag set?
- Is the blurb in the site's voice, and does it avoid claims the archive cannot support?
- Are the measured stats plausible for the archive size?
- Does the generated page render with the site's tokens, nav and motion, and no broken values?
- Is the digest the one CI will publish?

Merge only after the checks are green. Merging is the publication decision.
