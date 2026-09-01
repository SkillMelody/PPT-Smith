# PPT Smith V4 Bespoke 高定路线

> 路线边界：本文只描述 Bespoke。模板原生复用见
> [v4-template-route.md](v4-template-route.md)，三路线总览见
> [v4-three-route-architecture.md](v4-three-route-architecture.md)。

## 目标与决策权

Bespoke 面向视觉上限。高配模型拥有叙事、视觉编码、构图和几何决策权；
PPT Smith 只提供原材料整理、来源锁、原生可编辑门禁、真实渲染、视觉复审和
有限精修闭环。它不以 Standard 成品为起点，也不调用 Template 路线的
Component Atlas、strict plan 或模板页克隆器。

```text
源材料 + 用户目标 + 页数合同 + 参考模板（可选）
                         ↓
Content & Evidence Map → Narrative Director → Design Director
                         ↓
高配作者从空白 Presentation 创作原生对象
                         ↓
来源/数字/可编辑性/结构/真实渲染门禁
                         ↓
外部视觉复审 → 最多两轮定向精修
```

## 页数合同

Production Request 支持 `auto`、`target`、`range` 和 `exact`。内容评估必须给出
`minimum_viable_pages`、`recommended_pages` 和 `maximum_useful_pages`；不足时不
压缩丢内容，过多时不编造填充。

## 模板在 Bespoke 中的角色

模板只可作为 `style_transfer` 或 `inspiration` 视觉证据。Bespoke 从空白文稿创作，
因此不能宣称保留企业母版或受保护品牌资产，也不接受 `strict` 复用请求。严格复用
属于独立 Template 路线。

## Authoring Manifest

`python3 -m engine plan-bespoke` 生成哈希锁定的 manifest；
`python3 -m engine author-bespoke` 执行作者脚本并完成非视觉交付门禁；
`python3 -m engine review-bespoke` 接收与 deck、render report 哈希绑定的人工或视觉模型
复审。完整长稿还需 Narrative Contract，锁定受众决策、核心论点、章节任务、
Assertion–Evidence 和跨页推进，但禁止指定布局、坐标、构图或模板页。

## 验收状态

当前已具备 Production Request、页数协调、来源绑定、原生可编辑检查、真实渲染、
Bespoke 视觉底线与外部视觉复审门禁。尚未自动化的部分包括长文可信内容评估、
模板视觉解释、真实高配模型调用和按复审结果自动改写作者脚本。

## 不可跨越的边界

- Bespoke runtime 必须显式使用 `route="bespoke"` 的 QA 语义。
- Template 的组件碎片豁免不得作用于 Bespoke。
- Bespoke 输出目录不得包含 Template 路线的模板副本、组件清单或 strict-plan 中间件。
- Template 路线代码、样例和生成物不得在 Bespoke 专用 worktree 中继续开发。
