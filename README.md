# Skill Audit

<p align="center">
  <a href="#english">English</a> |
  <a href="#中文">中文</a>
</p>

<a id="english"></a>

## English

**Skill Audit** is a local workflow for auditing, evaluating, and improving Codex/Claude-style skills. It combines deterministic script checks with LLM-assisted review so skill instructions remain concise, executable, and aligned with real project workflows.

This skill adapts two complementary ideas:

- Codex-style skill design: progressive disclosure, clear trigger boundaries, and script-backed deterministic steps.
- Anthropic/Claude skill-creator practice: evaluate skills on realistic tasks, identify failure modes, and iterate from observed behavior.

It is not a wrapper around Claude's official tooling. It turns those principles into a portable audit workflow that can run inside a standalone skill repository or a larger project with a `skills/` directory.

### What It Checks

- Trigger boundaries: when the skill should and should not activate.
- Progressive disclosure: whether `SKILL.md` stays lean and loads details only when needed.
- Success criteria: whether outputs, validation points, and completion conditions are explicit.
- Cognitive load: whether the skill contains historical blame, excessive examples, or distracting process narration.
- Hallucination risk: whether it references unsupported slash commands, unavailable tools, or unverified platform behavior.
- Scriptable steps: whether deterministic tasks are handled by scripts instead of repeated LLM reasoning.
- Evaluation readiness: whether realistic prompts and regression cases can test the skill.

### Repository Layout

```text
skill-audit/
├── SKILL.md
├── README.md
├── LICENSE
├── references/
│   ├── review-rubric.md
│   └── eval-workflow.md
└── scripts/
    └── skill-audit.py
```

### Usage

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

After the script check, use `references/review-rubric.md` for semantic review. For real-task testing or version comparison, use `references/eval-workflow.md`.

### Review Output

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

### Design Boundary

The audit workflow separates deterministic checks from semantic judgment:

- Scripts check structure, file references, frontmatter, command mentions, resource links, and other repeatable issues.
- The reviewing agent judges trigger fit, progressive disclosure quality, generalization, overfitting, and whether real-task eval is needed.

This keeps skill review practical: scripts catch repeatable defects, while the LLM handles judgment that cannot be reduced to static rules.

### License

MIT License. See [LICENSE](LICENSE).

<a id="中文"></a>

## 中文

**Skill Audit** 是一个用于审查、评估和改进 Codex/Claude 风格 skill 的本地工作流。它把确定性脚本检查和 LLM 语义审查结合起来，让 skill 说明保持简洁、可执行，并能和真实项目流程对齐。

这个 skill 借鉴并转化了两类思路：

- Codex 风格的 skill 设计：渐进式披露、清晰触发边界、确定性步骤脚本化。
- Anthropic/Claude skill-creator 的实践：用真实任务评估 skill，发现失败模式，再基于实际表现迭代。

它不是 Claude 官方工具的封装，而是把这些原则转化为可移植的审查工作流；既可以在独立 skill 仓库中运行，也可以在包含 `skills/` 目录的大型项目中运行。

### 审查内容

- 触发边界：什么时候应该触发，什么时候不应该触发。
- 渐进式披露：`SKILL.md` 是否保持简洁，细节是否按需加载。
- 成功标准：输出、校验点和完成条件是否明确。
- 认知负担：是否存在历史纠错叙事、过度举例或干扰性的流程说明。
- 幻觉风险：是否引用了不支持的 slash command、不可用工具或未验证的平台能力。
- 脚本化机会：确定性步骤是否交给脚本，而不是反复依赖 LLM 推理。
- Eval 准备度：是否能用真实 prompt 和回归案例测试 skill。

### 目录结构

```text
skill-audit/
├── SKILL.md
├── README.md
├── LICENSE
├── references/
│   ├── review-rubric.md
│   └── eval-workflow.md
└── scripts/
    └── skill-audit.py
```

### 使用方式

审查当前仓库根目录的 skill：

```powershell
python .\scripts\skill-audit.py --write
```

在大型项目中审查单个 skill：

```powershell
python .\scripts\skill-audit.py --skill <skill-name-or-path> --write
```

批量审查项目 `skills/` 下的多个 skill：

```powershell
python .\scripts\skill-audit.py --all --write
```

JSON 报告会写入：

```text
data/skill-audit/<skill-name>-audit.json
```

脚本检查完成后，使用 `references/review-rubric.md` 做语义审查。需要真实任务测试或版本比较时，再使用 `references/eval-workflow.md`。

### 审查输出

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

### 设计边界

这个工作流把机械检查和语义判断分开：

- 脚本负责检查结构、文件引用、frontmatter、命令引用、资源链接等可重复问题。
- 审查 agent 负责判断触发边界、渐进式披露质量、泛化能力、是否过拟合示例，以及是否需要真实任务 eval。

这样可以让 skill 审查更务实：脚本捕捉可重复缺陷，LLM 处理无法静态规则化的判断。

### 许可证

MIT License。见 [LICENSE](LICENSE)。
