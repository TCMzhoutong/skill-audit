# Skill Audit

<p align="center">
  <a href="README.md"><strong>English</strong></a> ·
  <a href="README_CN.md">简体中文</a>
</p>

**Skill Audit** is a local workflow for auditing, evaluating, and improving Codex/Claude-style skills. It combines deterministic script checks with LLM-assisted review so skill instructions remain concise, executable, and aligned with real project workflows.

This skill adapts two complementary ideas:

- Codex-style skill design: progressive disclosure, clear trigger boundaries, and script-backed deterministic steps.
- Anthropic/Claude skill-creator practice: evaluate skills on realistic tasks, identify failure modes, and iterate from observed behavior.

It is not a wrapper around Claude's official tooling. It turns those principles into a portable audit workflow that can run inside a standalone skill repository or a larger project with a `skills/` directory.

## What It Checks

- Trigger boundaries: when the skill should and should not activate.
- Progressive disclosure: whether `SKILL.md` stays lean and loads details only when needed.
- Success criteria: whether outputs, validation points, and completion conditions are explicit.
- Cognitive load: whether the skill contains historical blame, excessive examples, or distracting process narration.
- Hallucination risk: whether it references unsupported slash commands, unavailable tools, or unverified platform behavior.
- Scriptable steps: whether deterministic tasks are handled by scripts instead of repeated LLM reasoning.
- Evaluation readiness: whether realistic prompts and regression cases can test the skill.

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

Install this repository as a skill in your Codex or Claude Code skills directory.

For Codex, you can use your normal skill installation flow or clone this repository into the skills directory used by your Codex environment. For Claude Code, install it the same way you install other local skills.

After installation, ask your coding agent to use the skill directly.

## Usage

Use natural-language requests such as:

```text
Use skill-audit to review this skill.
```

```text
Use skill-audit to audit skills/paper-card for progressive disclosure, trigger boundaries, excessive examples, hallucination risks, and scriptable steps.
```

```text
Use skill-audit to compare the current version of this skill with the previous version and suggest fixes.
```

The agent should:

1. Load `SKILL.md`.
2. Run the deterministic audit script when available.
3. Read `references/review-rubric.md` for semantic review.
4. Use `references/eval-workflow.md` when real-task evaluation or version comparison is needed.
5. Return findings, a fix plan, and whether an eval is needed.

## Optional Local Script Check

You can also run the bundled script manually before asking the agent for semantic review.

Audit the current repository root as a skill:

```powershell
python .\scripts\skill-audit.py --write
```

Audit one skill in a larger project:

```powershell
python .\scripts\skill-audit.py --skill <skill-name-or-path> --write
```

Audit all skills under a project-level `skills/` directory:

```powershell
python .\scripts\skill-audit.py --all --write
```

The JSON report is written under:

```text
data/skill-audit/<skill-name>-audit.json
```

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

## Design Boundary

The audit workflow separates deterministic checks from semantic judgment:

- Scripts check structure, file references, frontmatter, command mentions, resource links, and other repeatable issues.
- The reviewing agent judges trigger fit, progressive disclosure quality, generalization, overfitting, and whether real-task eval is needed.

This keeps skill review practical: scripts catch repeatable defects, while the LLM handles judgment that cannot be reduced to static rules.

## License

MIT License. See [LICENSE](LICENSE).
