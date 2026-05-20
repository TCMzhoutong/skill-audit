# Skill Audit

<p align="center">
  <a href="README.md"><strong>English</strong></a> ·
  <a href="README_CN.md">简体中文</a>
</p>

**Skill Audit** is a portable audit workflow for reviewing, testing, and improving agent Skills, including Codex/Claude/Perplexity-style Skill directories. It combines deterministic checks with LLM-assisted semantic review so Skills stay loadable, concise, maintainable, and aligned with real user requests.

## Design Sources

This Skill incorporates ideas from three public Skill-design traditions:

- Codex Skill design: progressive disclosure, bundled resources, script-backed deterministic steps, and concise runtime instructions.
- Anthropic/Claude Skill Creator guidance: realistic task evaluation, regression cases, and iterative improvement from observed failures.
- Perplexity Research: routing-oriented descriptions, context-cost discipline, dependency/frontmatter separation, gotcha-driven refinement, loading/resource/task evals, and action-at-a-distance checks.

New rules in the current version were added after reviewing Perplexity Research, **"Designing, Refining, and Maintaining Agent Skills at Perplexity"**:

https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity

## What It Checks

- Whether a task should be a Skill at all.
- Standard Skill directory structure.
- Resource placement: root files that should move into `references/`, `scripts/`, `assets/`, or `agents/`.
- Frontmatter rules:
  - `name` must exactly match the directory name.
  - `name` and directory name must be slug-style: lowercase letters, digits, and single hyphens.
  - `description` must start with `Load when...`.
  - `description` must be 50 words or fewer.
  - `description` should describe real user intent, not the Skill's workflow.
  - `depends` is checked as a simple list of dependent Skill names.
- Trigger boundaries, including should-load, should-not-load, and forbidden-load cases.
- Action at a distance: whether a new or changed Skill could steal requests from nearby Skills.
- Progressive disclosure and context cost.
- Railroading risks in `SKILL.md` body instructions.
- Gotchas distilled from real agent failures.
- Missing references, long reference files without navigation, unsupported tool/platform claims, and scriptable opportunities.

## Repository Layout

```text
skill-audit/
├── SKILL.md
├── README.md
├── README_CN.md
├── LICENSE
├── references/
│   ├── review-rubric.md
│   └── eval-workflow.md
└── scripts/
    └── skill-audit.py
```

## Installation

Install or clone this repository into the Skills directory used by your agent environment.

Example:

```bash
git clone https://github.com/TCMzhoutong/skill-audit.git ~/.codex/skills/skill-audit
```

Adjust the destination path for your local Codex, Claude Code, or other agent setup.

## Usage

Use natural-language requests such as:

```text
Use skill-audit to review this Skill.
```

```text
Use skill-audit to audit skills/paper-card for trigger boundaries, progressive disclosure, resource placement, and frontmatter issues.
```

```text
Use skill-audit to compare the current version of this Skill with the previous version and design regression evals.
```

The agent should:

1. Run the deterministic script when possible.
2. Read `SKILL.md`.
3. Read `references/review-rubric.md` for semantic review.
4. Read `references/eval-workflow.md` when testing, comparing versions, or designing evals.
5. Return findings first, then a fix plan and eval needs.

## Local Script

Audit the current repository root as a Skill:

```bash
python3 scripts/skill-audit.py --write
```

Audit one Skill:

```bash
python3 scripts/skill-audit.py --skill <skill-name-or-path> --write
```

Audit all Skills under a project-level `skills/` directory:

```bash
python3 scripts/skill-audit.py --all --write
```

The JSON report is written to:

```text
data/skill-audit/<skill-name>-audit.json
```

## Script Scope

The script is intentionally deterministic and conservative. It checks repeatable issues such as file structure, references, frontmatter shape, description wording, slug naming, root-file placement, long references, and obvious railroading signals.

The frontmatter parser is intentionally limited to scalar `name`/`description` values and simple list-style `depends` entries. Complex YAML should be reviewed manually or supported by extending the script.

## Review Output

```yaml
skill: <skill-name>
verdict: pass | needs_revision | blocked
script_check:
  ok: true
  report: data/skill-audit/<skill-name>-audit.json
findings:
  - severity: high | medium | low
    file: skills/<skill-name>/...
    line: 1
    issue: ""
    recommendation: ""
fix_plan:
  - ""
needs_eval: true | false
```

## License

MIT License. See [LICENSE](LICENSE).
