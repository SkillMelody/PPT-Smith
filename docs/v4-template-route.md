# PPT Smith V4 Template / Path C 路线

## 目标

Template 路线从哈希锁定的用户模板开始，只执行显式声明的原生图表、表格、文本和
reviewed Component Atlas 操作。它不调用 Bespoke 作者脚本，不让模型自由改写几何，
也不把 Standard 的布局策略套进模板。

## 生产链路

```text
只读模板 → Evidence Ledger → 逐页内容合同 → 内容完整性硬门禁
        → Template Evidence → reviewed Component Atlas
        → 语义/容量匹配 → strict plan → 原生对象绑定与克隆
        → 仅抽取目标交付页 → Template QA → 候选页真实渲染
```

`strict-template` 的最终 PPTX 只包含 strict plan 实际触达的目标页。完整模板副本仅存在于
自动清理的内部工作目录；未使用的模板页不会进入成品，也不会进入 `qa/candidate/slides`。

## 内容完整性门禁

交付候选必须同时提供 `--evidence-ledger` 和 `--content-bindings`。Ledger 将来源中的
claim、metric 和 exhibit 固定为可追踪证据单元；逐页合同声明 assertion、选用证据、
必需证据及有理由的省略。`strict-template` 在任何原生对象操作和 PPTX 写出之前检查：

- 加权证据覆盖率至少 90%；
- 必需证据处理率 100%；
- 数字证据选用率至少 95%；
- Exhibit 必须选用或给出明确省略理由；
- 正文页必须有 assertion 和已知 evidence ID；
- `要点 1`、`顺序`、`核心议题`、`阶段 3` 等通用占位文案不得进入交付候选。

缺少输入时返回 `CONTENT_INTEGRITY_REQUIRED`；合同或覆盖率不合格时返回
`CONTENT_INTEGRITY_FAILED`。通过报告会保存在结果的 `content_integrity` 字段中。

## QA 边界

Template 路线允许 reviewed 组件中 `bind:block:*:*:item/detail` 形成多个原生文本框，
因此其碎片检查可扣除这些已声明组件文本。该豁免只在 `route="template"` 生效；Standard
与 Bespoke 仍按全部文本框计算碎片度。

模板资产保真按交付文件的可达边界验证：输出中存在的母版、版式、主题和媒体必须与
源模板字节一致，且输出关系不得指向缺失资产；源模板中未被交付页引用的媒体无需复制。

## 集成测试边界

`tests/integration/test_template_content_integrity.py` 使用仓库内生成的三段报告，始终运行，
用于证明中段数字证据遗漏会被拒绝、完整证据会通过。它是可复现的内容完整性回归基线。

McKinsey Component Atlas 测试依赖未随仓库分发的参考模板，属于可选参考覆盖。安装后可将
`PPT_SMITH_MCKINSEY_FIXTURE` 指向包含 `sources/` 与 `analysis/` 的项目目录；未配置或目录
不存在时，`tests/integration/test_real_component_atlas.py` 会整组明确跳过。该跳过不能被
解释为真实模板验收通过，也不替代始终运行的生成式集成测试。

## 当前状态

已支持模板哈希、可达资产校验、证据账本、逐页内容合同、内容完整性硬门禁、原生
chart/table/text，Atlas 语义与容量匹配，多组件编排，以及漏斗、金字塔、时间线、图表
组件和固定原生组。完整长稿仍取决于模板组件审核覆盖率和内容拓扑匹配；无合适组件时
必须报告缺口，不能硬套。
