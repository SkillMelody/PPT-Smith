# PPT Smith V4 Template / Path C 路线

## 目标

Template 路线从哈希锁定的用户模板开始，只执行显式声明的原生图表、表格、文本和
reviewed Component Atlas 操作。它不调用 Bespoke 作者脚本，不让模型自由改写几何，
也不把 Standard 的布局策略套进模板。

## 生产链路

```text
只读模板 → Template Evidence → reviewed Component Atlas
        → 语义/容量匹配 → strict plan → 原生对象绑定与克隆
        → 仅抽取目标交付页 → Template QA → 候选页真实渲染
```

`strict-template` 的最终 PPTX 只包含 strict plan 实际触达的目标页。完整模板副本仅存在于
自动清理的内部工作目录；未使用的模板页不会进入成品，也不会进入 `qa/candidate/slides`。

## QA 边界

Template 路线允许 reviewed 组件中 `bind:block:*:*:item/detail` 形成多个原生文本框，
因此其碎片检查可扣除这些已声明组件文本。该豁免只在 `route="template"` 生效；Standard
与 Bespoke 仍按全部文本框计算碎片度。

## 当前状态

已支持模板哈希、母版/布局/主题/媒体资产校验，原生 chart/table/text，Atlas 语义与容量
匹配，多组件编排，以及漏斗、金字塔、时间线、图表组件和固定原生组。完整长稿仍取决于
模板组件审核覆盖率和内容拓扑匹配；无合适组件时必须报告缺口，不能硬套。
