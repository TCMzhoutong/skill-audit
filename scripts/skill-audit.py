#!/usr/bin/env python
"""Deterministic checks for project-local skills."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
OUT_ROOT = ROOT / "data" / "skill-audit"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


NEGATIVE_PATTERNS = [
    "不要",
    "不得",
    "不能",
    "不应该",
    "禁止",
    "严禁",
    "never",
    "do not",
    "don't",
    "must not",
]

PAST_ERROR_PATTERNS = [
    "之前错误",
    "上次错误",
    "之前的问题",
    "误删",
    "纠错",
    "修复之前",
]

ATTENTION_RISK_PATTERNS = [
    "claude -p",
    "/paper-card",
    "/精读",
    "anchor",
    "Source block",
    "block id",
    "NotebookLM 路径断了",
]

EXTRANEOUS_DOCS = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LOCAL_MD_REF_RE = re.compile(r"(?:Read|见|参见|读取|打开)\s+`([^`]+\.md)`")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, [{"severity": "error", "issue": "missing_frontmatter"}]

    frontmatter: dict[str, str] = {}
    current_key = ""
    for raw in match.group(1).splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            if value in {"|-", "|", ">-", ">"}:
                frontmatter[current_key] = ""
            else:
                frontmatter[current_key] = value.strip("\"'")
            continue
        if current_key and raw.startswith((" ", "\t")):
            frontmatter[current_key] = (frontmatter[current_key] + "\n" + raw.strip()).strip()

    return frontmatter, text[match.end() :], findings


def line_hits(text: str, patterns: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    lower_patterns = [(pattern, pattern.casefold()) for pattern in patterns]
    for lineno, line in enumerate(text.splitlines(), start=1):
        folded = line.casefold()
        for pattern, lowered in lower_patterns:
            if lowered in folded:
                hits.append({"line": lineno, "pattern": pattern, "text": line.strip()[:220]})
    return hits


def resolve_skill_path(value: str) -> Path:
    raw = Path(value)
    if raw.exists():
        return raw
    candidate = SKILLS_ROOT / value
    if candidate.exists():
        return candidate
    raise SystemExit(f"skill not found: {value}")


def iter_skill_paths(args: argparse.Namespace) -> list[Path]:
    if args.all:
        if not SKILLS_ROOT.exists():
            if (ROOT / "SKILL.md").exists():
                return [ROOT]
            raise SystemExit("skills/ not found and current repository has no SKILL.md")
        return sorted(
            path
            for path in SKILLS_ROOT.iterdir()
            if path.is_dir() and not path.name.startswith("_") and (path / "SKILL.md").exists()
        )
    if not args.skill:
        if (ROOT / "SKILL.md").exists():
            return [ROOT]
        raise SystemExit("pass --skill <name-or-path> or --all")
    return [resolve_skill_path(args.skill)]


def referenced_md_files(skill_dir: Path, body: str) -> list[str]:
    refs: list[str] = []
    for match in LOCAL_MD_REF_RE.finditer(body):
        ref = match.group(1)
        if not ref or ref.startswith(("http://", "https://")):
            continue
        if any(token in ref for token in ["<", ">", "*", "?", "..."]):
            continue
        refs.append(ref)
    return sorted(set(refs))


def inline_md_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"`([^`]+\.md)`", text):
        ref = match.group(1)
        if ref.startswith(("http://", "https://")):
            continue
        if re.search(r"\s|\+", ref):
            continue
        if ("/" not in ref and "\\" not in ref) and ref.casefold() == "skill.md":
            continue
        if any(token in ref for token in ["<", ">", "*", "?", "..."]):
            continue
        refs.append(ref)
    return refs


def check_references(skill_dir: Path, refs: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for ref in refs:
        path = (skill_dir / ref).resolve()
        try:
            path.relative_to(skill_dir.resolve())
        except ValueError:
            findings.append({"severity": "warning", "issue": "reference_outside_skill", "reference": ref})
            continue
        if not path.exists():
            findings.append({"severity": "error", "issue": "missing_reference", "reference": ref})
    return findings


def attention_hits(text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    slash_command_re = re.compile(r"(?<![A-Za-z0-9_.-])/(?:paper-card|精读)(?![A-Za-z0-9_.-])")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in ["claude -p", "anchor", "Source block", "block id", "NotebookLM 路径断了"]:
            if pattern.casefold() in line.casefold():
                hits.append({"line": lineno, "pattern": pattern, "text": line.strip()[:220]})
        if slash_command_re.search(line):
            hits.append({"line": lineno, "pattern": "custom_slash_command", "text": line.strip()[:220]})
    return hits


def has_toc(text: str) -> bool:
    head = "\n".join(text.splitlines()[:30]).casefold()
    return "目录" in head or "table of contents" in head or "toc" in head


def audit_skill(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    findings: list[dict[str, Any]] = []
    if not skill_md.exists():
        return {
            "skill": skill_dir.name,
            "path": str(skill_dir.relative_to(ROOT)),
            "ok": False,
            "findings": [{"severity": "error", "issue": "missing_SKILL.md"}],
        }

    text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, body, fm_findings = parse_frontmatter(text)
    findings.extend(fm_findings)

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not name:
        findings.append({"severity": "error", "issue": "frontmatter_missing_name"})
    elif skill_dir.resolve() != ROOT.resolve() and name != skill_dir.name:
        findings.append({"severity": "error", "issue": "frontmatter_name_mismatch", "name": name, "folder": skill_dir.name})
    if not description:
        findings.append({"severity": "error", "issue": "frontmatter_missing_description"})
    elif len(description) < 80:
        findings.append({"severity": "warning", "issue": "description_may_undertrigger", "chars": len(description)})

    line_count = len(text.splitlines())
    if line_count > 500:
        findings.append({"severity": "warning", "issue": "skill_md_over_500_lines", "lines": line_count})

    refs = referenced_md_files(skill_dir, body)
    expanded_refs = set(refs)
    for ref in refs:
        ref_path = skill_dir / ref
        if ref_path.exists():
            for child_ref in inline_md_refs(ref_path.read_text(encoding="utf-8-sig", errors="replace")):
                expanded_refs.add(str((ref_path.parent / child_ref).relative_to(skill_dir)))
    refs = sorted(expanded_refs)
    findings.extend(check_references(skill_dir, refs))

    for path in skill_dir.rglob("*.md"):
        if path.name == "SKILL.md":
            continue
        rel = str(path.relative_to(skill_dir))
        ref_text = path.read_text(encoding="utf-8-sig", errors="replace")
        ref_lines = len(ref_text.splitlines())
        if ref_lines > 300 and not has_toc(ref_text):
            findings.append({"severity": "warning", "issue": "long_reference_without_toc", "file": rel, "lines": ref_lines})

    for path in skill_dir.iterdir():
        if path.is_file() and path.name in EXTRANEOUS_DOCS and path.name != "README.md":
            findings.append({"severity": "warning", "issue": "extraneous_doc_file", "file": path.name})

    negative_hits = line_hits(text, NEGATIVE_PATTERNS)
    if len(negative_hits) > 12:
        findings.append({"severity": "warning", "issue": "many_negative_constraints", "count": len(negative_hits), "sample": negative_hits[:8]})

    for category, patterns, severity in [
        ("past_error_language", PAST_ERROR_PATTERNS, "warning"),
    ]:
        hits = line_hits(text, patterns)
        if hits:
            findings.append({"severity": severity, "issue": category, "count": len(hits), "sample": hits[:8]})
    hits = attention_hits(text)
    if hits:
        findings.append({"severity": "warning", "issue": "attention_risk_language", "count": len(hits), "sample": hits[:8]})

    # Detect local Markdown files that are not pointed to from SKILL.md. This is
    # a warning, not an error: some files can be intentionally loaded by scripts.
    referenced_paths = {str((skill_dir / ref).resolve()) for ref in refs}
    unreferenced = []
    for path in skill_dir.rglob("*.md"):
        if path.name == "SKILL.md" or path.name == "README.md":
            continue
        if str(path.resolve()) not in referenced_paths:
            unreferenced.append(str(path.relative_to(skill_dir)))
    if unreferenced:
        findings.append({"severity": "info", "issue": "unreferenced_markdown_resources", "files": unreferenced[:20]})

    ok = not any(item.get("severity") == "error" for item in findings)
    return {
        "skill": skill_dir.name,
        "path": "." if skill_dir.resolve() == ROOT.resolve() else str(skill_dir.relative_to(ROOT)),
        "ok": ok,
        "metrics": {
            "skill_md_lines": line_count,
            "description_chars": len(description),
            "referenced_md_count": len(refs),
        },
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="skill name under skills/ or path to a skill folder")
    parser.add_argument("--all", action="store_true", help="audit all project-local skills")
    parser.add_argument("--write", action="store_true", help="write JSON report under data/skill-audit")
    args = parser.parse_args()

    reports = [audit_skill(path) for path in iter_skill_paths(args)]
    output: dict[str, Any]
    if len(reports) == 1:
        output = reports[0]
    else:
        output = {
            "ok": all(report["ok"] for report in reports),
            "count": len(reports),
            "reports": reports,
        }

    if args.write:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
        name = "all" if args.all else reports[0]["skill"]
        out_path = OUT_ROOT / f"{name}-audit.json"
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        output["written"] = str(out_path.relative_to(ROOT))

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
