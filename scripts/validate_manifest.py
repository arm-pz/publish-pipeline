#!/usr/bin/env python3
"""Validate site/skills.json and site/deny.json before any build or deploy.

Usage: python validate_manifest.py <skills.json> [deny.json]
Exit 1 on any error.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REPO_RE = re.compile(r"[^/\s]+/[^/\s]+\Z")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
PAGES = {"bespoke", "generated", "none"}
TAGS = {
    "editorial", "seo", "discovery", "career", "learning",
    "arena", "decisions", "authoring", "release", "performance",
}


def load(path: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"ERROR {path}: not found")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR {path}: invalid JSON: {exc}")


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2

    errors: list[str] = []
    manifest = load(sys.argv[1])
    if not isinstance(manifest, dict):
        print("ERROR manifest: top level must be an object")
        return 1

    if manifest.get("schema") != 1:
        errors.append("manifest.schema must be 1")
    site = manifest.get("site")
    if not isinstance(site, str) or not site.startswith("https://"):
        errors.append("manifest.site must be an https URL")

    groups = manifest.get("groups")
    if not isinstance(groups, list) or not groups:
        errors.append("manifest.groups must be a non-empty array")
        groups = []

    group_ids: set[str] = set()
    group_orders: set[int] = set()
    for i, group in enumerate(groups):
        where = f"groups[{i}]"
        if not isinstance(group, dict):
            errors.append(f"{where} must be an object")
            continue
        gid = group.get("id")
        if not isinstance(gid, str) or not NAME_RE.fullmatch(gid):
            errors.append(f"{where}.id must be a lowercase hyphenated id")
        elif gid in group_ids:
            errors.append(f"{where}.id duplicates {gid}")
        else:
            group_ids.add(gid)
        for key in ("title", "descriptor"):
            value = group.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}.{key} must be a non-empty string")
        order = group.get("order")
        if not isinstance(order, int) or isinstance(order, bool):
            errors.append(f"{where}.order must be an integer")
        elif order in group_orders:
            errors.append(f"{where}.order duplicates {order}")
        else:
            group_orders.add(order)

    skills = manifest.get("skills")
    if not isinstance(skills, list) or not skills:
        errors.append("manifest.skills must be a non-empty array")
        skills = []

    names: set[str] = set()
    skill_orders: set[int] = set()
    pages = 0
    for i, skill in enumerate(skills):
        where = f"skills[{i}]"
        if not isinstance(skill, dict):
            errors.append(f"{where} must be an object")
            continue
        name = skill.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{where}.name must be a lowercase hyphenated name")
        elif name in names:
            errors.append(f"{where}.name duplicates {name}")
        else:
            names.add(name)

        if not isinstance(skill.get("title"), str) or not skill["title"].strip():
            errors.append(f"{where}.title must be a non-empty string")

        install = skill.get("install")
        if install is not None and (not isinstance(install, str) or not install.strip()):
            errors.append(f"{where}.install must be a non-empty string when present")
        page_title = skill.get("pageTitle")
        if page_title is not None and (not isinstance(page_title, str) or not page_title.strip()):
            errors.append(f"{where}.pageTitle must be a non-empty string when present")

        repo = skill.get("repo")
        path = skill.get("path")
        legacy = skill.get("legacy")
        if repo is None:
            if not isinstance(legacy, dict):
                errors.append(f"{where}.repo null requires a legacy object")
            else:
                archive = legacy.get("archive")
                if not isinstance(archive, str) or not archive.strip():
                    errors.append(f"{where}.legacy.archive must be a path")
                if not isinstance(legacy.get("sha256"), str) or not SHA_RE.fullmatch(legacy["sha256"]):
                    errors.append(f"{where}.legacy.sha256 must be 64 lowercase hex characters")
                if not isinstance(legacy.get("description"), str) or not legacy["description"].strip():
                    errors.append(f"{where}.legacy.description must be a non-empty string")
            if path is not None:
                errors.append(f"{where}.path must be null for a legacy entry")
        else:
            if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
                errors.append(f"{where}.repo must be owner/name")
            elif isinstance(name, str) and repo.split("/")[-1] != name:
                errors.append(f"{where}.repo basename must equal the skill name {name}")
            if path not in (".", name, f"skills/{name}"):
                errors.append(
                    f"{where}.path must be '.', '{name}' or 'skills/{name}' for a repo-backed entry"
                )
            if legacy is not None:
                errors.append(f"{where}.legacy is only allowed when repo is null")

        if skill.get("group") not in group_ids:
            errors.append(f"{where}.group must reference an existing group id")
        if skill.get("tag") not in TAGS:
            errors.append(f"{where}.tag must be one of {sorted(TAGS)}")
        page = skill.get("page")
        if page not in PAGES:
            errors.append(f"{where}.page must be one of {sorted(PAGES)}")
        elif page != "none":
            pages += 1
            for key in ("blurb", "stats"):
                value = skill.get(key)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{where}.{key} is required when page is not 'none'")

        if page == "generated":
            if repo is None:
                errors.append(f"{where}: a legacy entry cannot have a generated page")
            source = skill.get("pageSource")
            if not isinstance(source, dict):
                errors.append(f"{where}.pageSource is required for a generated page")
            else:
                description = source.get("description")
                if not isinstance(description, str) or not description.strip():
                    errors.append(f"{where}.pageSource.description must be a non-empty string")
                files = source.get("files")
                if not isinstance(files, list) or not files:
                    errors.append(f"{where}.pageSource.files must be a non-empty array")
                else:
                    valid = True
                    for j, item in enumerate(files):
                        fw = f"{where}.pageSource.files[{j}]"
                        if not isinstance(item, dict):
                            errors.append(f"{fw} must be an object")
                            valid = False
                            continue
                        if not isinstance(item.get("path"), str) or not item["path"].strip():
                            errors.append(f"{fw}.path must be a non-empty string")
                            valid = False
                        for key in ("lines", "bytes"):
                            value = item.get(key)
                            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                                errors.append(f"{fw}.{key} must be a non-negative integer")
                                valid = False
                    if valid:
                        if source.get("fileCount") != len(files):
                            errors.append(
                                f"{where}.pageSource.fileCount must equal len(files)")
                        if source.get("lines") != sum(item["lines"] for item in files):
                            errors.append(
                                f"{where}.pageSource.lines must equal the sum of file lines")
                size = source.get("bytes")
                if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                    errors.append(f"{where}.pageSource.bytes must be a positive integer")
                license_id = source.get("license")
                if not isinstance(license_id, str) or not license_id.strip():
                    errors.append(f"{where}.pageSource.license must be a non-empty string")
                if not isinstance(source.get("commit"), str) or not COMMIT_RE.fullmatch(source["commit"]):
                    errors.append(f"{where}.pageSource.commit must be 40 lowercase hex characters")
                if not isinstance(source.get("sha256"), str) or not SHA_RE.fullmatch(source["sha256"]):
                    errors.append(f"{where}.pageSource.sha256 must be 64 lowercase hex characters")
        elif "pageSource" in skill:
            errors.append(f"{where}.pageSource is only allowed on a generated page")

        order = skill.get("order")
        if not isinstance(order, int) or isinstance(order, bool):
            errors.append(f"{where}.order must be an integer")
        elif order in skill_orders:
            errors.append(f"{where}.order duplicates {order}")
        else:
            skill_orders.add(order)

    if len(sys.argv) == 3:
        deny = load(sys.argv[2])
        if not isinstance(deny, list):
            errors.append("deny.json must be a top-level array")
        else:
            denied: set[str] = set()
            for i, entry in enumerate(deny):
                where = f"deny[{i}]"
                if not isinstance(entry, dict):
                    errors.append(f"{where} must be an object")
                    continue
                repo = entry.get("repo")
                if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
                    errors.append(f"{where}.repo must be owner/name")
                elif repo in denied:
                    errors.append(f"{where}.repo duplicates {repo}")
                else:
                    denied.add(repo)
                reason = entry.get("reason")
                if not isinstance(reason, str) or not reason.strip():
                    errors.append(f"{where}.reason must be a non-empty string")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"{len(errors)} error(s)")
        return 1

    print(f"OK {len(skills)} skills, {len(groups)} groups, {pages} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
