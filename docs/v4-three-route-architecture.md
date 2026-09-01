# PPT Smith V4 三路线架构

V4 有三条并列生产路线，不是两条路线加一个藏在 Bespoke 内的模板功能。

| 路线 | 决策权 | 主要入口 | 质量目标 |
| --- | --- | --- | --- |
| Standard / Engineering | 引擎决定布局与视觉 | `python3 -m engine compile` | 确定、可重复的工程下限 |
| Bespoke | 高配模型决定叙事、视觉与几何 | `plan-bespoke` / `author-bespoke` | 模型能力所能达到的视觉上限 |
| Template / Path C | 用户模板与 reviewed 组件合同决定可复用边界 | `strict-template` 及组件工具链 | 严格原生复用、品牌资产保真 |

三条路线共享来源核验、包检查和真实渲染能力，但不共享决策权，也不默认共享 QA
豁免。请求的 `route` 必须是 `standard`、`bespoke` 或 `template`；入口与请求路线不匹配
时直接拒绝。

## 执行隔离

- 每项路线任务使用独立注册的 Git worktree；不能借用另一条路线的任务 ID、分支或目录。
- 路线源码、测试与样例按模块归属维护；共享代码只保留路线无关机制。
- 路线特有 QA 规则必须显式接收 `route`，禁止修改全局默认后让其他路线被动继承。
- 交付物只有一个主 PPTX；模板、工作副本、QA 图片和最终内容各自分区。

## 目录约定

```text
run-root/
  inputs/
    template/          # 用户模板，只读
    content/           # 原材料与来源文档
  work/                # strict plan、Atlas、临时工作副本
  deliverables/        # 只放最终候选 PPTX/报告
  qa/
    candidate/slides/  # 只渲染最终候选页
    reference/         # 仅显式请求参考渲染时创建，可按模板哈希复用
```

Template 路线不会在每次执行时把模板参考页重新写进候选稿 `slides/`；默认只渲染候选
交付页。模板分析与模板渲染证据应按模板 SHA-256 缓存，而不是跟每次成品生成绑定。
