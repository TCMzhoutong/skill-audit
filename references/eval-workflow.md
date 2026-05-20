# Skill Eval Workflow

用于真实任务测试、版本比较和迭代改进。只在用户要求“测试这个 skill”“比较修改前后”“做 eval”时读取。

## 1. 定义测试集

为目标 Skill 写真实 prompt，分三类：

- loading eval：该加载、不可加载、近邻误触发。
- resource eval：加载后是否读取正确的 `references/`、调用正确的 `scripts/`、使用正确的 `assets/`。
- task eval：端到端是否完成真实任务。

最小集合：

- 8-12 条 should-trigger 查询，使用真实用户表达。
- 8-12 条 should-not-trigger 查询，覆盖近邻 Skill 和共享关键词。
- 6-10 条 forbidden-load 查询，覆盖 3-5 个相邻 Skill，检查 action at a distance。
- 3-5 条端到端任务，覆盖常规、边界和已知失败类型。

保存到：

```text
data/skill-audit/<skill-name>-evals.json
```

结构：

```json
{
  "skill_name": "<skill-name>",
  "evals": [
    {
      "id": "normal-1",
      "prompt": "用户真实会说的话",
      "should_load": true,
      "must_not_load": ["neighbor-skill"],
      "expected_resources": ["references/example.md"],
      "expected": ["可客观检查的结果"],
      "notes": "人工审查关注点"
    }
  ]
}
```

## 2. 运行方式

当前本地原型优先人工驱动：用这些 prompt 真实调用 skill，保存输出、命令结果和修改文件。需要并行独立验证时，经用户明确授权后再使用子代理。

输出目录：

```text
data/skill-audit/<skill-name>-workspace/
└── iteration-1/
    └── <eval-id>/
        ├── prompt.md
        ├── outputs/
        ├── commands.md
        └── review.json
```

## 3. 断言

优先写可程序化断言：

- `description` 是否以 `Load when...` 开头
- `description` 是否不超过 50 词
- `name` 是否与目录名逐字符一致
- `name` 和目录名是否是合法 slug
- `depends` 是否是合法 Skill 名称列表
- 标准目录结构是否合规
- 文件是否创建
- 合法标题是否通过
- 是否没有流程泄漏词
- 是否没有引用不存在文件

语义质量用人工 review：

- 是否解决用户真实任务
- 是否过拟合例子
- 是否输出冗余流程说明
- 是否把确定性步骤交给脚本
- 是否被正确加载或正确拒绝加载
- 是否读取了必要资源且没有加载无关大文件
- 是否在错误发生后停下来恢复，而不是继续执行后续命令

## 4. 迭代

每轮只根据真实失败改 skill：

1. 汇总失败类型。
2. 判断应改 `description`、`SKILL.md`、引用文件还是脚本。
3. 修改后重跑同一 eval。
4. 新增覆盖失败类型的回归案例。
5. 如果失败来自 agent 翻车，优先沉淀为短 gotcha，而不是扩写流程。
6. 只要改过 `description`，必须重跑 should-trigger、should-not-trigger 和 forbidden-load eval；如果新增或移除触发边界，同步更新这些查询。

## 5. 描述触发评估

生成 8-12 条 should-trigger 和 8-12 条 should-not-trigger 查询，覆盖：

- 明确命名 skill 的请求
- 不命名 skill 但任务明显匹配的请求
- 与相邻 skill 共享关键词但意图不同的近邻负例

再生成 6-10 条 forbidden-load 查询，覆盖 3-5 个相邻 Skill。先人工确认查询集，再调整 frontmatter `description`。`description` 应匹配用户真实表达，不写 Skill 的内部 workflow。
