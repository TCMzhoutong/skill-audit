---
name: skill-audit
description: Load when the user asks to review, test, fix, or improve an agent Skill, Codex/Claude/Perplexity-style Skill, compare Skill versions, design Skill evals, or check whether a Skill should load.
---

# Skill Audit

审查和迭代 Codex/Claude/Perplexity 风格 Skill。重点判断：是否值得做成 Skill、是否会被正确加载、是否控制上下文成本、是否把确定性检查交给脚本。

## 快速入口

先运行确定性审查：

```bash
python3 scripts/skill-audit.py --skill <skill-name-or-path> --write
```

审查当前仓库根目录的 skill：

```bash
python3 scripts/skill-audit.py --write
```

批量审查项目 `skills/` 下的多个 skill：

```bash
python3 scripts/skill-audit.py --all --write
```

脚本通过后，按用户目的选择读取：

- 只做文档审查：Read `references/review-rubric.md`
- 要做真实任务测试或版本比较：Read `references/eval-workflow.md`

## 审查流程

1. 运行 `skill-audit.py`，报告可脚本化问题。
2. 读取目标 skill 的 `SKILL.md` 正文，只按引用继续读取必要资源。
3. 用 `references/review-rubric.md` 输出结构化审查。
4. 若用户要求修正，先修可脚本化问题，再修语义边界。
5. 修正后重跑 `skill-audit.py`；涉及具体产出质量时补跑真实任务 eval。

## 必查重点

- 目录结构：根目录只保留 `SKILL.md` 和可选 `agents/`、`scripts/`、`references/`、`assets/`；多余 README、安装说明、速查、变更日志应移除或并入必要资源。
- Frontmatter：`name` 必须与目录名逐字符一致；`description` 必须以 `Load when...` 开头、50 词以内、描述真实用户意图，不描述工作流。
- 依赖：`depends` 只声明其他 Skill 名称。递归加载依赖是宿主 loader 的职责；审查时只校验字段结构和本地依赖是否存在。
- 正文：写给模型看，只保留目标、约束、选择依据、失败恢复和 gotchas；避免把模型已经知道的通用命令写成固定流水线。

## Gotchas

- 不把 frontmatter 当作模型运行时正文审查；宿主系统应先解析配置并剥离 frontmatter，再把正文交给模型。
- 不把 Perplexity、Claude 或 Codex 某一家的平台字段硬套到所有 Skill；先区分强制标准、可选扩展和当前宿主不支持的能力。
- 发现长命令序列时先判断它是不是脆弱流程；如果只是常规操作，改成目标和恢复原则，或沉淀为脚本。

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
- LLM 负责判断触发边界、正文是否 railroading、gotcha 是否来自真实失败、语义泛化、是否需要真实 eval。
- Claude 官方命令只作为设计参考；本项目不调用 Claude 专属 CLI、eval viewer 或打包命令。
