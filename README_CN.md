# Skill Audit

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_CN.md"><strong>简体中文</strong></a>
</p>

**Skill Audit** 是一个用于审查、评估和改进 Codex/Claude 风格 skill 的本地工作流。它把确定性脚本检查和 LLM 语义审查结合起来，让 skill 说明保持简洁、可执行，并能和真实项目流程对齐。

这个 skill 借鉴并转化了两类思路：

- Codex 风格的 skill 设计：渐进式披露、清晰触发边界、确定性步骤脚本化。
- Anthropic/Claude skill-creator 的实践：用真实任务评估 skill，发现失败模式，再基于实际表现迭代。

它不是 Claude 官方工具的封装，而是把这些原则转化为可移植的审查工作流；既可以在独立 skill 仓库中运行，也可以在包含 `skills/` 目录的大型项目中运行。

## 审查内容

- 触发边界：什么时候应该触发，什么时候不应该触发。
- 渐进式披露：`SKILL.md` 是否保持简洁，细节是否按需加载。
- 成功标准：输出、校验点和完成条件是否明确。
- 认知负担：是否存在历史纠错叙事、过度举例或干扰性的流程说明。
- 幻觉风险：是否引用了不支持的 slash command、不可用工具或未验证的平台能力。
- 脚本化机会：确定性步骤是否交给脚本，而不是反复依赖 LLM 推理。
- Eval 准备度：是否能用真实 prompt 和回归案例测试 skill。

## 目录结构

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

把这个仓库安装到你的 Codex 或 Claude Code skills 目录中。

安装方式可以沿用你当前环境里其他 skill 的安装方式，例如 clone 到 Codex 识别的 skills 目录，或者使用你平时的本地 skill 安装流程。安装完成后，直接让编码代理调用这个 skill。

## 使用方式

通过自然语言触发：

```text
Use skill-audit to review this skill.
```

```text
Use skill-audit to audit skills/paper-card for progressive disclosure, trigger boundaries, excessive examples, hallucination risks, and scriptable steps.
```

```text
Use skill-audit to compare the current version of this skill with the previous version and suggest fixes.
```

代理应该：

1. 读取 `SKILL.md`。
2. 如有需要，先运行确定性审查脚本。
3. 读取 `references/review-rubric.md` 做语义审查。
4. 需要真实任务测试或版本比较时，读取 `references/eval-workflow.md`。
5. 返回发现、修正计划，以及是否需要 eval。

## 可选的本地脚本检查

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

## 设计边界

这个工作流把机械检查和语义判断分开：

- 脚本负责检查结构、文件引用、frontmatter、命令引用、资源链接等可重复问题。
- 审查 agent 负责判断触发边界、渐进式披露质量、泛化能力、是否过拟合示例，以及是否需要真实任务 eval。

这样可以让 skill 审查更务实：脚本捕捉可重复缺陷，LLM 处理无法静态规则化的判断。

## 许可证

MIT License。见 [LICENSE](LICENSE)。
