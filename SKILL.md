---
name: skill-audit
description: Audit, evaluate, and improve Codex/Claude-style skills. Use when the user asks to review a skill,校正 skill, compare skill versions, design skill evals, check progressive disclosure, triggering boundaries, excessive examples, negative constraints, hallucination risks, scriptable steps, or whether a skill follows Claude/Codex skill-creator principles.
---

# Skill Audit

审查和迭代 Codex/Claude 风格 skill。目标是把 Claude 官方 skill-creator 的“真实任务评估 + 迭代改进”和 Codex skill-creator 的“渐进式披露 + 脚本化确定性步骤”落成可执行工作流。

## 快速入口

先运行确定性审查：

```powershell
python .\scripts\skill-audit.py --skill <skill-name-or-path> --write
```

审查当前仓库根目录的 skill：

```powershell
python .\scripts\skill-audit.py --write
```

批量审查项目 `skills/` 下的多个 skill：

```powershell
python .\scripts\skill-audit.py --all --write
```

脚本通过后，按用户目的选择读取：

- 只做文档审查：Read `references/review-rubric.md`
- 要做真实任务测试或版本比较：Read `references/eval-workflow.md`

## 审查流程

1. 运行 `skill-audit.py`，报告可脚本化问题。
2. 读取目标 skill 的 `SKILL.md`，只按引用继续读取必要资源。
3. 用 `references/review-rubric.md` 输出结构化审查。
4. 若用户要求修正，先修可脚本化问题，再修语义边界。
5. 修正后重跑 `skill-audit.py`；涉及具体产出质量时补跑真实任务 eval。

## 输出

审查输出用这个结构：

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

## 边界

- 运行脚本能判断的事项交给 `scripts/skill-audit.py`。
- LLM 负责判断触发边界、渐进式披露质量、语义泛化、是否过拟合例子、是否需要真实 eval。
- Claude 官方命令只作为设计参考；本项目不调用 Claude 专属 CLI、eval viewer 或打包命令。
