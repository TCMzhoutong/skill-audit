#!/usr/bin/env python3
"""Deterministic checks for project-local skills.

Frontmatter parsing is intentionally limited to scalar name/description values
and simple list-style depends entries. Extend it before relying on nested YAML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = Path.cwd().resolve()
SKILLS_ROOT = WORK_ROOT / "skills"
OUT_ROOT = WORK_ROOT / "data" / "skill-audit"


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
    "README_CN.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LOCAL_MD_REF_RE = re.compile(r"(?:Read|见|参见|读取|打开)\s+`([^`]+\.md)`")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STANDARD_TOP_LEVEL_DIRS = {"agents", "assets", "references", "scripts"}
STANDARD_TOP_LEVEL_FILES = {"SKILL.md", ".gitignore", "LICENSE"}
SCRIPT_EXTENSIONS = {".bash", ".js", ".mjs", ".ps1", ".py", ".rb", ".sh", ".ts"}
ASSET_EXTENSIONS = {
    ".csv",
    ".docx",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".json",
    ".otf",
    ".pdf",
    ".png",
    ".pptx",
    ".svg",
    ".ttf",
    ".xlsx",
}
RESOURCE_DIRS = {"agents", "assets", "references", "scripts"}
RESOURCE_PATH_RE = re.compile(
    r"(?P<path>(?:\.?[\\/])?(?:skills[\\/][A-Za-z0-9_-]+[\\/])?"
    r"(?:agents|assets|references|scripts)[\\/][^\s`'\"<>|]+)"
)
AGENT_METADATA_NAMES = {"openai.yaml", "openai.yml"}
DESCRIPTION_WORKFLOW_PATTERNS = [
    "workflow",
    "steps",
    "first",
    "then",
    "after that",
    "will",
    "先",
    "然后",
    "接着",
    "最后",
    "步骤",
    "流程",
    "工作流",
]
DESCRIPTION_CAPABILITY_PATTERNS = [
    "this skill",
    "the skill",
    "provides",
    "helps",
    "can ",
    "supports",
    "用于",
    "这个 skill",
    "本 skill",
    "能力",
]
USER_INTENT_HINTS = [
    "asks",
    "wants",
    "needs",
    "requests",
    "user",
    "用户",
    "请求",
    "想",
    "需要",
    "让我",
    "帮我",
]
COMMAND_LINE_RE = re.compile(
    r"^\s*(?:\d+[.)]\s*)?(?:python|python3|node|npm|pnpm|yarn|uv|pip|git|gh|cargo|go|ruby|bundle|make|bash|sh|sed|awk|rg|grep)\b"
)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, [{"severity": "error", "issue": "missing_frontmatter"}]

    frontmatter: dict[str, Any] = {}
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
            elif value == "":
                frontmatter[current_key] = []
            else:
                frontmatter[current_key] = value.strip("\"'")
            continue
        if current_key and raw.startswith((" ", "\t")):
            item_match = re.match(r"^\s*-\s+(.+?)\s*$", raw)
            if isinstance(frontmatter.get(current_key), list) and item_match:
                frontmatter[current_key].append(item_match.group(1).strip("\"'"))
            elif isinstance(frontmatter.get(current_key), str):
                frontmatter[current_key] = (frontmatter[current_key] + "\n" + raw.strip()).strip()

    return frontmatter, text[match.end() :], findings


def scalar(value: Any) -> str:
    return value if isinstance(value, str) else ""


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?|[\u4e00-\u9fff]", text))


def pattern_hits(text: str, patterns: list[str]) -> list[str]:
    folded = text.casefold()
    return [pattern for pattern in patterns if pattern.casefold() in folded]


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
        return raw.resolve()
    candidate = SKILLS_ROOT / value
    if candidate.exists():
        return candidate.resolve()
    personal_candidate = SCRIPT_ROOT.parent / value
    if personal_candidate.exists():
        return personal_candidate.resolve()
    raise SystemExit(f"skill not found: {value}")


def iter_skill_paths(args: argparse.Namespace) -> list[Path]:
    if args.all:
        if not SKILLS_ROOT.exists():
            if (WORK_ROOT / "SKILL.md").exists():
                return [WORK_ROOT]
            raise SystemExit("skills/ not found and current repository has no SKILL.md")
        return sorted(
            path
            for path in SKILLS_ROOT.iterdir()
            if path.is_dir() and not path.name.startswith("_") and (path / "SKILL.md").exists()
        )
    if not args.skill:
        if (WORK_ROOT / "SKILL.md").exists():
            return [WORK_ROOT]
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


def normalize_ref_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def check_local_resource_paths(skill_dir: Path, files: list[tuple[Path, str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_findings: set[tuple[str, int, str, str]] = set()
    skill_root = skill_dir.resolve()
    skill_prefix = f"skills/{skill_dir.name}/"
    seen_files: set[str] = set()
    for file_path, text in files:
        file_key = str(file_path.resolve())
        if file_key in seen_files:
            continue
        seen_files.add(file_key)
        try:
            rel_file = str(file_path.relative_to(skill_root))
        except ValueError:
            rel_file = str(file_path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in RESOURCE_PATH_RE.finditer(line):
                raw = match.group("path").rstrip(".,);]")
                normalized = normalize_ref_path(raw)
                if normalized.endswith("/") or normalized.endswith("\\"):
                    continue
                if any(token in normalized.casefold() for token in ["example", "<", ">", "..."]):
                    continue
                if normalized.startswith(skill_prefix):
                    key = (rel_file, lineno, raw, "skill_internal_resource_uses_project_relative_path")
                    if key not in seen_findings:
                        findings.append(
                            {
                                "severity": "warning",
                                "issue": "skill_internal_resource_uses_project_relative_path",
                                "file": rel_file,
                                "line": lineno,
                                "path": raw,
                                "recommendation": "Use a path relative to this Skill root, such as scripts/..., references/..., assets/..., or agents/....",
                            }
                        )
                        seen_findings.add(key)
                    normalized = normalized[len(skill_prefix) :]
                top = normalized.split("/", 1)[0]
                if top in RESOURCE_DIRS:
                    local_resource = skill_root / normalized
                    shared_resource = WORK_ROOT / normalized
                    if local_resource.exists():
                        continue
                    if shared_resource.exists():
                        line_key = line.casefold()
                        if "shared project resource" in line_key or "shared project script" in line_key or "共享" in line:
                            continue
                        key = (rel_file, lineno, raw, "resource_reference_resolves_to_project_root_not_skill")
                        if key not in seen_findings:
                            findings.append(
                                {
                                    "severity": "warning",
                                    "issue": "resource_reference_resolves_to_project_root_not_skill",
                                    "file": rel_file,
                                    "line": lineno,
                                    "path": raw,
                                    "recommendation": "If this resource belongs to the Skill, move it under the Skill directory; otherwise state that it is a shared project resource.",
                                }
                            )
                            seen_findings.add(key)
                        continue
                    key = (rel_file, lineno, raw, "missing_resource_reference")
                    if key not in seen_findings:
                        findings.append(
                            {
                                "severity": "error",
                                "issue": "missing_resource_reference",
                                "file": rel_file,
                                "line": lineno,
                                "path": raw,
                                "recommendation": "Skill resource paths should resolve from the Skill root unless explicitly marked as shared project resources.",
                            }
                        )
                        seen_findings.add(key)
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


def check_standard_structure(skill_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    unexpected: list[str] = []
    root_markdown: list[str] = []
    root_scripts: list[str] = []
    root_assets: list[str] = []
    root_agent_metadata: list[str] = []
    for path in skill_dir.iterdir():
        if path.is_dir() and path.name not in STANDARD_TOP_LEVEL_DIRS:
            unexpected.append(path.name + "/")
        elif path.is_file() and path.name not in STANDARD_TOP_LEVEL_FILES:
            unexpected.append(path.name)
            suffix = path.suffix.casefold()
            if suffix == ".md":
                root_markdown.append(path.name)
            elif suffix in SCRIPT_EXTENSIONS:
                root_scripts.append(path.name)
            elif suffix in ASSET_EXTENSIONS:
                root_assets.append(path.name)
            elif path.name.casefold() in AGENT_METADATA_NAMES:
                root_agent_metadata.append(path.name)
    if unexpected:
        findings.append(
            {
                "severity": "warning",
                "issue": "nonstandard_top_level_entries",
                "entries": sorted(unexpected),
                "recommendation": "Keep root entries to SKILL.md plus optional agents/, scripts/, references/, assets/.",
            }
        )
    if root_markdown:
        findings.append(
            {
                "severity": "warning",
                "issue": "root_markdown_should_move_to_references",
                "files": sorted(root_markdown),
                "recommendation": "Move explanatory Markdown resources into references/ and update relative links from SKILL.md.",
            }
        )
    if root_scripts:
        findings.append(
            {
                "severity": "warning",
                "issue": "root_script_should_move_to_scripts",
                "files": sorted(root_scripts),
                "recommendation": "Move executable reusable files into scripts/ and update any command paths.",
            }
        )
    if root_assets:
        findings.append(
            {
                "severity": "warning",
                "issue": "root_asset_should_move_to_assets",
                "files": sorted(root_assets),
                "recommendation": "Move templates, media, binary, and sample data files into assets/ unless they are meant to be read as references.",
            }
        )
    if root_agent_metadata:
        findings.append(
            {
                "severity": "warning",
                "issue": "root_agent_metadata_should_move_to_agents",
                "files": sorted(root_agent_metadata),
                "recommendation": "Move UI-facing agent metadata into agents/.",
            }
        )
    return findings


def check_skill_name_slug(value: str, field: str) -> list[dict[str, Any]]:
    if SKILL_NAME_RE.fullmatch(value):
        return []
    return [
        {
            "severity": "error",
            "issue": f"{field}_invalid_slug",
            "value": value,
            "recommendation": "Use lowercase letters, digits, and single hyphens only, for example skill-audit.",
        }
    ]


def parse_depends(value: Any) -> tuple[list[str], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if value in (None, "", []):
        return [], findings
    if isinstance(value, list):
        deps = [item for item in value if isinstance(item, str)]
        if len(deps) != len(value):
            findings.append({"severity": "error", "issue": "frontmatter_depends_non_string_item"})
        return deps, findings
    if isinstance(value, str):
        if "," in value:
            deps = [item.strip() for item in value.split(",") if item.strip()]
            findings.append(
                {
                    "severity": "warning",
                    "issue": "frontmatter_depends_inline_csv",
                    "recommendation": "Prefer YAML list form: depends: followed by - skill-name entries.",
                }
            )
            return deps, findings
        return [value], findings
    findings.append({"severity": "error", "issue": "frontmatter_depends_invalid_type"})
    return [], findings


def check_depends(skill_dir: Path, frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    deps, dep_findings = parse_depends(frontmatter.get("depends"))
    findings.extend(dep_findings)
    if not deps:
        return findings
    seen: set[str] = set()
    duplicates: list[str] = []
    for dep in deps:
        if dep in seen:
            duplicates.append(dep)
        seen.add(dep)
        if dep == skill_dir.name:
            findings.append({"severity": "error", "issue": "frontmatter_depends_self", "dependency": dep})
        if "\n" in dep or not dep.strip():
            findings.append({"severity": "error", "issue": "frontmatter_depends_invalid_name", "dependency": dep})
        if SKILLS_ROOT.exists() and not (SKILLS_ROOT / dep).is_dir() and skill_dir.parent == SKILLS_ROOT:
            findings.append({"severity": "warning", "issue": "frontmatter_depends_missing_local_skill", "dependency": dep})
    if duplicates:
        findings.append({"severity": "warning", "issue": "frontmatter_depends_duplicates", "dependencies": sorted(set(duplicates))})
    return findings


def check_description(description: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not description:
        findings.append({"severity": "error", "issue": "frontmatter_missing_description"})
        return findings
    words = word_count(description)
    if not description.startswith("Load when "):
        findings.append(
            {
                "severity": "error",
                "issue": "description_must_start_load_when",
                "recommendation": 'Start with "Load when..." and describe the user intent that should trigger the Skill.',
            }
        )
    if words > 50:
        findings.append({"severity": "error", "issue": "description_over_50_words", "words": words})
    workflow_hits = pattern_hits(description, DESCRIPTION_WORKFLOW_PATTERNS)
    if workflow_hits:
        findings.append(
            {
                "severity": "warning",
                "issue": "description_may_describe_workflow",
                "patterns": workflow_hits[:8],
                "recommendation": "Describe real user intent, not the sequence the Skill will follow.",
            }
        )
    capability_hits = pattern_hits(description, DESCRIPTION_CAPABILITY_PATTERNS)
    if capability_hits:
        findings.append(
            {
                "severity": "warning",
                "issue": "description_may_describe_skill_capability",
                "patterns": capability_hits[:8],
                "recommendation": "Prefer phrases users would say or ask for over describing what the Skill is.",
            }
        )
    if not pattern_hits(description, USER_INTENT_HINTS):
        findings.append(
            {
                "severity": "info",
                "issue": "description_lacks_user_intent_language",
                "recommendation": "Check whether the description uses words from real user requests.",
            }
        )
    return findings


def check_body_style(body: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    command_lines = []
    in_fence = False
    for lineno, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and COMMAND_LINE_RE.match(line):
            command_lines.append({"line": lineno, "text": stripped[:180]})
    if len(command_lines) >= 8:
        findings.append(
            {
                "severity": "warning",
                "issue": "possible_railroading_command_sequence",
                "count": len(command_lines),
                "sample": command_lines[:8],
                "recommendation": "Replace rigid command sequences with goals, constraints, recovery guidance, or scripts.",
            }
        )
    if not re.search(r"(?im)^#{1,3}\s*(gotchas?|注意事项|易错|陷阱|失败)", body):
        findings.append(
            {
                "severity": "info",
                "issue": "missing_gotchas_section",
                "recommendation": "For mature Skills, add concise gotchas distilled from real agent failures.",
            }
        )
    return findings


def audit_skill(skill_dir: Path) -> dict[str, Any]:
    skill_md = skill_dir / "SKILL.md"
    findings: list[dict[str, Any]] = []
    if not skill_md.exists():
        try:
            rel_path = str(skill_dir.relative_to(WORK_ROOT))
        except ValueError:
            rel_path = str(skill_dir)
        return {
            "skill": skill_dir.name,
            "path": rel_path,
            "ok": False,
            "findings": [{"severity": "error", "issue": "missing_SKILL.md"}],
        }

    text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, body, fm_findings = parse_frontmatter(text)
    findings.extend(fm_findings)
    findings.extend(check_standard_structure(skill_dir))
    findings.extend(check_skill_name_slug(skill_dir.name, "directory_name"))

    name = scalar(frontmatter.get("name", ""))
    description = scalar(frontmatter.get("description", ""))
    if not name:
        findings.append({"severity": "error", "issue": "frontmatter_missing_name"})
    else:
        findings.extend(check_skill_name_slug(name, "frontmatter_name"))
        if name != skill_dir.name:
            findings.append({"severity": "error", "issue": "frontmatter_name_mismatch", "name": name, "folder": skill_dir.name})
    findings.extend(check_description(description))
    findings.extend(check_depends(skill_dir, frontmatter))

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
    scanned_files: list[tuple[Path, str]] = [(skill_md, text)]
    for ref in refs:
        ref_path = skill_dir / ref
        if ref_path.exists():
            scanned_files.append((ref_path, ref_path.read_text(encoding="utf-8-sig", errors="replace")))
    findings.extend(check_local_resource_paths(skill_dir, scanned_files))

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
    findings.extend(check_body_style(body))

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

    try:
        rel_skill_path = "." if skill_dir == WORK_ROOT else str(skill_dir.relative_to(WORK_ROOT))
    except ValueError:
        rel_skill_path = str(skill_dir)

    ok = not any(item.get("severity") == "error" for item in findings)
    return {
        "skill": skill_dir.name,
        "path": rel_skill_path,
        "ok": ok,
        "metrics": {
            "skill_md_lines": line_count,
            "description_chars": len(description),
            "description_words": word_count(description),
            "name_is_valid_slug": bool(SKILL_NAME_RE.fullmatch(name)),
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
        output["written"] = str(out_path.relative_to(WORK_ROOT))

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
