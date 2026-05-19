# Skill Eval Workflow

用于真实任务测试、版本比较和迭代改进。只在用户要求“测试这个 skill”“比较修改前后”“做 eval”时读取。

## 1. 定义测试集

为目标 skill 写 3-5 个真实 prompt：

- 常规成功案例
- 边界案例
- 近邻 skill 容易误触发的案例
- 已知失败类型的回归案例

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

- 文件是否创建
- frontmatter 字段是否存在
- 合法标题是否通过
- 是否没有流程泄漏词
- 是否没有引用不存在文件

语义质量用人工 review：

- 是否解决用户真实任务
- 是否过拟合例子
- 是否输出冗余流程说明
- 是否把确定性步骤交给脚本

## 4. 迭代

每轮只根据真实失败改 skill：

1. 汇总失败类型。
2. 判断应改 `description`、`SKILL.md`、引用文件还是脚本。
3. 修改后重跑同一 eval。
4. 新增覆盖失败类型的回归案例。

## 5. 描述触发评估

生成 8-12 条 should-trigger 和 8-12 条 should-not-trigger 查询，覆盖：

- 明确命名 skill 的请求
- 不命名 skill 但任务明显匹配的请求
- 与相邻 skill 共享关键词但意图不同的近邻负例

先人工确认查询集，再调整 frontmatter `description`。
