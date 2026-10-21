# Trigger cases for publish-pipeline

Written to the format in `tune-skill/references/test-cases.md`. The skill under test is
`publish-pipeline`, judged from its `description` frontmatter only, as an agent deciding what to
load would. Competing descriptions read for these cases: `publish-release-gate`, `upstream-check`,
`release-gate`, `web-preflight`, `draft-skill`, `tune-skill`, `skill-launch`, and `findable`.

**Run:** hand-run on 2026-10-20 against the descriptions only. No automated triggering loop was
run; none exists here.

## Cases

| # | Message | Expected skill | Pass condition | Result |
|---|---|---|---|---|
| 1 | "Set up CI/CD so every new skill repo I push gets its own page on skills.caffeinity.com." | publish-pipeline | names the PR gate and the three jobs; does not start deploying | PASS ("CI/CD or automation for a skills site") |
| 2 | "My new skill has been on GitHub for two days and the site still doesn't list it." | publish-pipeline | audits discovery and the manifest before changing anything | PASS ("asks why a skill is missing") |
| 3 | "The publish workflow went red after I added a skill. Fix it." | publish-pipeline | names the failing gate before editing | PASS ("needs a red publish run diagnosed") |
| 4 | "The deploy said success but the new page is still the old one." | publish-pipeline | distinguishes deploy from live verification; uses a cache-buster | PASS ("its page is stale") |
| 5 | "A repo looks like a valid skill but the site never picked it up. Why?" | publish-pipeline | walks the shape test clauses and the deny list | PASS ("asks why a skill is missing") |
| 6 | "Publish tune-skill to the marketplace and build its tarball." | publish-release-gate | publish-pipeline does not load as the publisher | PASS ("Not for releasing one skill through the marketplace, tarball or plugin channels") |
| 7 | "What haven't I pushed from these clones?" | upstream-check | publish-pipeline does not load | PASS ("Not for checking unpushed work") |
| 8 | "Is the site safe to launch tonight?" | release-gate | publish-pipeline does not load | PASS ("Not for deciding whether a build is safe to launch") |
| 9 | "Review this SKILL.md's trigger wording." | tune-skill | publish-pipeline does not load | PASS ("Not for writing and tuning a skill") |
| 10 | "Why does the live site list more skills than GitHub has repos?" | upstream-check | publish-pipeline does not load; this is catalogue-vs-repos drift | PASS ("listing drift" clause; publish-pipeline owns manifest-vs-surfaces, not repo inventory) |
| 11 | "Make my new skill's site page more discoverable." | findable / findable-polish | publish-pipeline does not load | PASS: no "discoverability" claim in the description |

## Boundary pairs

| Message | Should trigger | Why |
|---|---|---|
| "Deploy the skill site after I finish this skill" | publish-release-gate | one skill through the existing channels, manual |
| "Make the site publish future skills automatically" | publish-pipeline | changes the machine, not one release |
| "The manifest and the live hub disagree" | publish-pipeline | generator or deploy drift inside one surface set |
| "The site lists skills GitHub no longer has" | upstream-check | catalogue against the repo inventory |
| "Add this skill to the manifest" | publish-pipeline | admission is the manifest's job |
| "Audit this skill's description" | tune-skill | the skill's behaviour, not the site |

Spans both: "set up the pipeline and then publish the new skill through it" → `publish-pipeline`
first (install and prove the machine), then `publish-release-gate` for the one-off release if the
user does not want to wait for discovery. publish-pipeline must not claim to publish the single
skill through the marketplace.

Manual-path conflict: "Copy the tarball and hand-edit `.well-known/agent-skills/index.json` like the
old checklist says" → on a site with this pipeline, `publish-pipeline` wins and the manual index
edit is superseded; on a site without one, `publish-release-gate` owns the manual path. Pass
condition: names which path applies and does not run both against the same site.

## Not verified

- Which skill an agent picks when `publish-release-gate` and this skill are both loaded and the
  request mixes "pipeline" with "publish my skill"; only the descriptions were compared.
- Whether the shape-test or workflow instructions work against a real repo: the machine was
  implemented in `arm-pz/skills-site` on 2026-10-21 and its pull-request check job has run green;
  the publish, rollback and discovery proofs have not been run.
