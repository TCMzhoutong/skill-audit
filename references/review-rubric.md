# Skill Review Rubric

用于人工语义审查。先看 `scripts/skill-audit.py` 的 JSON，再读目标 skill。

## 审查项

### 1. 是否应该是 Skill

- 任务需要专门知识、稳定流程、工具集成、脚本或随附资源。
- 如果一句系统提示、普通文档或一次性命令就能解决，建议不要做成 Skill。
- 快速变化的外部 API、个人临时偏好、项目一次性流程不应默认固化成 Skill。

### 2. 标准目录结构

- 根目录只保留 `SKILL.md` 和可选 `agents/`、`scripts/`、`references/`、`assets/`。
- 包管理例外：允许 `.gitignore` 和 `LICENSE`。
- `scripts/` 放可执行、确定性、可复用步骤。
- 属于某个 Skill 的资源必须放在该 Skill 目录下：脚本进 `scripts/`，说明性 Markdown 进 `references/`，模板和样例等进 `assets/`，agent 元数据进 `agents/`。
- 只有多个 Skill 或项目初始化共用的资源才放项目根目录；引用时必须明确标注为 shared project resource。
- Skill 文档中引用本 Skill 资源时，使用相对 Skill 根目录的 `scripts/...`、`references/...`、`assets/...`、`agents/...`，不要写 `skills/<skill-name>/...`。
- `references/` 放按需加载的说明、领域知识、复杂规则。
- `assets/` 放输出会使用但不该读入上下文的模板、图片、字体、样例文件。
- README、安装指南、速查、变更日志等人类项目文档通常不属于 Skill 运行资产。
- 如果根目录已有文件实际属于上述类别，必须重组到标准目录：说明性 Markdown 进 `references/`，可执行文件进 `scripts/`，模板/图片/字体/样例/二进制资源进 `assets/`，UI 元数据进 `agents/`。
- 重组后必须更新 `SKILL.md` 和引用文件里的相对路径，避免引用断裂。

### 3. Frontmatter

- `name` 必须与目录名逐字符一致，包括大小写、空格、连字符。
- `name` 和目录名必须是 slug：只使用小写字母、数字和单个连字符。
- `description` 必须以 `Load when...` 开头。
- `description` 控制在 50 词以内。
- `description` 描述用户真实意图或用户会说的话，不描述 Skill 是什么。
- `description` 不描述工作流，不写“先做 A 再做 B”。
- 修改 `description` 后必须重跑 should-trigger、should-not-trigger 和 forbidden-load eval。
- `depends` 只声明其他 Skill 名称；递归加载由宿主 loader 处理。
- 当前脚本只做受限 frontmatter 解析，支持标量 `name`、`description` 和简单列表式 `depends`；复杂 YAML 需人工确认或扩展脚本。
- Frontmatter 是给系统解析的配置；审查正文时假设模型只看到剥离 frontmatter 后的 Markdown 正文和按需资源。

### 4. 触发边界

- 近邻 Skill 的分工清楚，有 should-trigger 和 should-not-trigger 查询支撑。
- 新增或修改 Skill 时检查 action at a distance：列出 3-5 个相邻 Skill，确认本 Skill 的 `description` 不会抢走它们的请求。
- forbidden-load 查询应覆盖共享关键词、相同文件类型、相同工具链和相似动词。
- 描述能匹配真实请求，例如“帮我盯着这个 PR”，而不是抽象的“监控 pull request 状态变化”。
- 不写当前环境不支持的触发方式。

### 5. 渐进式披露

- `SKILL.md` 保留核心流程和资源导航。
- 细节放入直接可见的引用文件，且 SKILL.md 明确何时读取。
- 可执行脚本、模板、资产放在合适位置；脚本优先承担确定性步骤。
- 超过 100 行的引用文件有目录或快速定位方式。

### 6. 正文质量

- 正文写给模型看，不写给人类学习者看。
- 写目标、约束、判断依据、失败恢复策略，而不是轨道化命令流水线。
- 命令序列只在操作脆弱、必须严格复现时出现；否则改成脚本或原则。
- 每条正文内容都应回答：没有它，模型会不会更容易做错。

### 7. Gotchas

- 记录来自真实失败的高信号注意事项。
- gotcha 要短、具体、可迁移，说明触发条件和正确处理。
- 不把 gotchas 扩写成大段历史复盘或责备过去错误。
- 新 gotcha 应配套一个回归 eval。

### 8. 上下文成本

- 删除通用常识、系统提示重复内容、显而易见的命令解释。
- 示例服务于泛化，不围绕单一案例硬编码。
- 否定式约束转为正向边界；保留必要硬约束和 gotchas。
- 重内容放入 `references/`，可执行细节放入 `scripts/`。

### 9. 幻觉风险

- 不引用不存在的 slash command、工具、文件或平台能力。
- 不把未验证的外部工具流程写成默认可用。
- 外部生态内容改写成本项目可执行流程。

### 10. 脚本化机会

- 文件存在、frontmatter、目录结构、合法标题、命令参数、缓存状态等交给脚本。
- LLM 只处理语义判断、取舍、综合、解释和用户沟通。

## 审查结论

结论分三档：

- `pass`：可直接使用，仅有低风险建议。
- `needs_revision`：能用，但存在触发、渐进披露或输出边界问题。
- `blocked`：会误导执行、依赖不存在能力，或缺少关键脚本/文件。
