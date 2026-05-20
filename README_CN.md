# Skill Audit

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_CN.md"><strong>简体中文</strong></a>
</p>

**Skill Audit** 是一个用于审查、测试和改进 agent Skill 的可移植工作流，适用于 Codex/Claude/Perplexity 风格的 Skill 目录。它把确定性脚本检查和 LLM 语义审查结合起来，让 Skill 保持可加载、简洁、可维护，并且能匹配真实用户请求。

## 设计来源

这个 Skill 综合参考了三类公开的 Skill 设计思路：

- Codex Skill 设计：渐进式披露、随附资源、确定性步骤脚本化、简洁运行指令。
- Anthropic/Claude Skill Creator 思路：真实任务评估、回归案例、基于实际失败迭代。
- Perplexity Research：面向路由的 description、上下文成本控制、frontmatter 与正文分离、依赖声明、gotcha 驱动迭代、loading/resource/task eval，以及 action-at-a-distance 检查。

当前版本新增规则参考了 Perplexity Research 的文章 **“Designing, Refining, and Maintaining Agent Skills at Perplexity”**：

https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity

## 审查内容

- 一个任务是否真的应该做成 Skill。
- 标准 Skill 目录结构。
- 资源归位：根目录文件是否应该移动到 `references/`、`scripts/`、`assets/` 或 `agents/`。
- Frontmatter 规则：
  - `name` 必须与目录名完全一致。
  - `name` 和目录名必须是 slug：只使用小写字母、数字和单个连字符。
  - `description` 必须以 `Load when...` 开头。
  - `description` 必须控制在 50 词以内。
  - `description` 应描述真实用户意图，而不是 Skill 的工作流。
  - `depends` 会按简单依赖 Skill 名称列表检查。
- 触发边界，包括 should-load、should-not-load 和 forbidden-load。
- Action at a distance：新增或修改 Skill 是否会抢走相邻 Skill 的请求。
- 渐进式披露和上下文成本。
- `SKILL.md` 正文是否存在 railroading 风险。
- 是否有来自真实 agent 失败的 gotchas。
- 缺失引用、长 reference 缺少导航、不支持的工具/平台说法、可脚本化机会等。

## 仓库结构

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

## 安装

把这个仓库安装或 clone 到你的 agent 环境使用的 Skills 目录。

示例：

```bash
git clone https://github.com/TCMzhoutong/skill-audit.git ~/.codex/skills/skill-audit
```

如果你使用 Claude Code 或其他 agent 环境，请把目标路径替换成对应的本地 Skills 目录。

## 使用方式

可以用自然语言触发：

```text
Use skill-audit to review this Skill.
```

```text
Use skill-audit to audit skills/paper-card for trigger boundaries, progressive disclosure, resource placement, and frontmatter issues.
```

```text
Use skill-audit to compare the current version of this Skill with the previous version and design regression evals.
```

代理应该：

1. 尽可能先运行确定性脚本。
2. 读取 `SKILL.md`。
3. 读取 `references/review-rubric.md` 做语义审查。
4. 在测试、版本比较或设计 eval 时读取 `references/eval-workflow.md`。
5. 先返回发现，再给出修正计划和是否需要 eval。

## 本地脚本

审查当前仓库根目录的 Skill：

```bash
python3 scripts/skill-audit.py --write
```

审查单个 Skill：

```bash
python3 scripts/skill-audit.py --skill <skill-name-or-path> --write
```

批量审查项目级 `skills/` 目录下的 Skill：

```bash
python3 scripts/skill-audit.py --all --write
```

JSON 报告会写入：

```text
data/skill-audit/<skill-name>-audit.json
```

## 脚本范围

脚本保持确定性和保守性。它检查文件结构、引用、frontmatter 形状、description 写法、slug 命名、根目录资源归位、长 reference、明显的 railroading 信号等可重复问题。

当前 frontmatter 解析器是受限解析，只支持标量 `name`/`description` 和简单列表式 `depends`。复杂 YAML 需要人工确认，或先扩展脚本。

## 审查输出

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

## 许可证

MIT License。见 [LICENSE](LICENSE)。
