# MeowClaw PPT Smith

<p align="center">
  <img src="assets/branding/pptsmith-github-zh.png" alt="MeowClaw PPT Smith 图标" width="836">
</p>

> [English](README.en.md) · [Skill 执行入口](SKILL.md) · [工作流](references/declarative-design.md) · [可编辑样例](assets/samples/v5.1-no-image-policy-native.pptx)

把源文档、设计图或原生 PPT 模板，转成有来源、有真实预览、可以继续修改的演示文稿。模型负责理解内容和设计页面，固定后端负责生成原生对象与核验交付。

**当前版本：`5.2.1`。** 公共标识为 `meowclaw-pptsmith`，兼容安装名为 `article-html-to-ppt`、`meowclaw-decksmith`；许可证为 Apache-2.0。

## 开发中：从用户任务明确内容边界

本轮调整使用入口与制作指导：从实际交付目标判断哪些内容需要保留、哪些允许分析或调整，按需补问关键缺口。见[用户任务与内容边界](references/user-task-intent.md)。这是基于 5.2.1 的迭代，尚未发布新版本，不改变任务格式或运行时门禁。

另补充[图形语义检查](references/decorative-business-design.md#3-从内容关系到页面构图)：核对增减方向、逐项对应与并行时序，并说明可编辑形状与自动联动图表的区别。此项指导不改变使用方法，也不代表所有任务的效果已经验证。

**新增色彩与视觉语言指导：** 按当前品牌、内容和用户指定的参考选择背景对比、主辅色与强调、字图尺度和装饰承载；复用这些关系时继续让主体随内容变化。没有固定色板、色系禁用表或统一正文框架。对标时需记录具体页面的视觉退步，技术检查通过不能替代视觉目标达成。见[设计指导](references/decorative-business-design.md#色彩关系与视觉语言)及[逐页计划](templates/decorative-page-plan.md)。

该增量仍属开发中，版本保持 `5.2.1`，仅更新作者与审核指导，未改引擎、schema或使用入口；本轮仅做静态检查，优化后的成稿实测尚未启动，是否启动由用户决定。

## v5.2.1 更新：构图多样，全册规整，叙事完整

- **分开检查三个维度**：正文构图随内容变化，标题、导航、字体层级与图形线条保持统一；整册分别检查多样性、规整度和叙事完整性。
- **先规划章节与收尾**：根据汇报场景安排目录、章节、总结、决策与结束页，调整后同步页码与目录。短简报不强制增加章节或感谢页。
- **增强构图诊断**：`composition-check` 增加正文主结论对象的位置、字体及页面角色顺序，帮助定位需要读图复核的页面；这些信息不等于审美评分或语义验收。
- **沉淀两轮实稿经验**：新增[经营复盘两轮修订案例](references/cases/business-deck-diversity-coherence.md)，更新设计指南、页面规划表和完整对象的审核要求。疑似碰撞需回到实际页面核查。

使用入口、任务格式和原有警告规则保持兼容，旧任务无需迁移。本次改进集中在规划、诊断和复核，没有新增自动经营分析引擎，也未扩充原生图表类型。历史预览及验证记录保留原始版本标注；仓库版本号不代表各安装平台已同步发布。

## 从你的实际任务开始

在已经配置好运行环境的 Agent 中加载本 Skill，上传材料并说明需要交付什么。下面是三种任务的说法，选择贴近的一条即可，无需填写配置表。

**已有审核材料，按要求制作：**

```text
使用 PPT Smith，把附件中已经审核的材料做成汇报 PPT。
保留现有结论、数字和指标口径，可以重排信息、压缩重复表述；
标出的引文必须原文保留。参考附件的视觉风格，交付可编辑 PPTX 和实际预览。
```

**允许辅助分析材料，形成汇报：**

```text
使用 PPT Smith，根据这些资料制作项目评审汇报，供评审人讨论下一阶段安排。
可以梳理重点、比较方案并提出有依据的建议，区分原始事实与补充判断。
影响结论的资料缺口先指出，不补造原因、数字或责任人。
交付可编辑 PPTX 和实际预览。
```

**继续修改原有 PPT Smith 任务：**

```text
继续这个 PPT Smith 任务：用新数据更新第 4 页，把第 7 页结论改成附件中的表述。
保留其他页面的内容和设计；检查更新是否影响相关图表、摘要或页码，
超出本次修改范围的影响先说明。提供修改后的 PPTX 和预览。
```

局部修改示例需要保留原任务资料与状态，不代表可无损修改任意第三方 PPTX。上传材料本身不等于要求逐字保留；有“不得删改”“固定页序”或指定原文要求时请明确说明，Agent 按这些约束组织制作。

已有的受众、用途、时长或页数、模板及目标软件要求可随材料提供。语言、报告期间和业务口径仅在与任务相关时提取或补问，不是每份 PPT 的必填项。Agent 先阅读资料，只补问影响正确性或交付的关键缺口，并负责路线选择、对象描述、渲染与检查，用户无需编写 JSON 或记住命令。详见[用户任务与内容边界](references/user-task-intent.md)。

首次使用需准备支持本地工具的 Agent、Python 依赖、办公渲染器和字体，见[安装与本地自检](#安装与本地自检)；更多输入示例见[怎么用](#怎么用把目标交给-agent)。

<details>
<summary>示例：用经营资料制作管理层汇报</summary>

```text
使用 PPT Smith，根据附件经营报表和业务说明，制作约 15 页月度经营分析 PPT。
面向管理层，重点解释目标差距、变化来源和下一步需要决策的事项。
采用克制、规整的咨询式表达，结论先行，正文结构按内容选择。
已有数据保留口径和来源，缺失信息列明，推测原因与已证实事实分开。
先检查材料缺口，再制作；交付可编辑 PPTX 和实际预览。
```

经营分析是可选的业务场景，咨询式汇报是组织结论与证据的方法，数据可视化负责表达比较、趋势、结构和贡献。当前可用现有工作流制作这类汇报，质量仍取决于材料、模型与实际复核；“咨询式”不代表咨询公司的官方模板或质量认证。

</details>

<details>
<summary>v5.2.0 更新回顾：装饰商务设计与整册精修</summary>

## v5.2.0 更新：装饰商务设计与整册精修

- **新增可选 `decorative_business` 审核配置**：面向装饰商务汇报与原创模板，逐页先规划内容关系、阅读路径、图形的信息承载方式，以及主结论、证据、细节三个层次。
- **新增构图诊断 `composition-check`**：汇总已声明的构图，提示连续重复和单一结构占比过高的情况，供作者和审核者定位问题。它只做诊断，不给审美打分，也不认证原创性。
- **增加独立整册审核**：启用配置后，逐页通过还不够；须检查最终合并稿的构图节奏、图文归属和视觉层次。审核与具体构建、内容和设计证据的哈希绑定，整册结论不会随未变页的审核记录一起继承。
- **补充设计指南与精修案例**：把“只换颜色”“信息增加后全是表格”“异形图加零散小字”等反复出现的问题，写成逐页设计与修订方法。

**使用入口保持不变**，仍是 `create`、`recreate`、`template`。装饰商务任务可在初始化时增加 `--review-profile decorative_business`；未启用该配置的旧任务沿用原合同，无需补填构图字段。普通用户直接向 Agent 说明风格和要求即可，示例见[怎么用](#怎么用把目标交给-agent)。下方历史样例保留原始版本与统计口径。

</details>

## 作品画廊

以下收录 `assets/samples/` 中的示例图，按**图片首次加入仓库的日期倒序**排列；日期不是 PPT 的制作日期。点击缩略图查看原图，较早的设计与架构示例可展开查看。可编辑对象数仅对应各自的交付 PPTX，历史案例的验证范围见下文。

<p>
  <a href="assets/samples/v5.2-xiaomi-q2-h1-22page-overview.png"><img src="assets/samples/v5.2-xiaomi-q2-h1-22page-overview.png" alt="小米集团2025年第二季度及上半年经营复盘，22页装饰商务PPT实际渲染总览" width="100%"></a><br>
  <strong>2026-10-18 · 小米经营复盘 · 22 页装饰商务实测</strong><br>
  <small>本次合入能力的开发分支实测 · 519 个原生对象，含 6 个图表、4 个表格 · 点击查看完整预览</small>
</p>

<details>
<summary>查看本次实测的版本与验证范围</summary>

以用户提供的《小米集团 2025 年第二季度及上半年经营复盘》资料与数据底表制作，完成真实渲染、多轮修订和独立 Agent 审核。图片直接来自最终 PPTX 的 22 页预览。实测使用开发提交 `af23320`，当时版本文件仍为 `5.1.1`；相关能力已纳入 `5.2.0`，未将历史运行改写为正式版测试。

PPT 含 370 个文本、139 个形状/路径、6 个原生图表、4 个原生表格，共 519 个原生对象，图片对象为 0。Linux + LibreOffice 中的文字、表格修改已验证保存后重开保留；图表数据在应用内的修改未完成有效验证，PowerPoint/WPS 未实测。使用阿里巴巴普惠体，字体未嵌入。本处公开总览图，原始资料、完整日志和证据包不随仓库分发。

</details>

<table>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/v5.1-template-image-guided-4page-2col-overview.png"><img src="assets/samples/v5.1-template-image-guided-4page-2col-overview.png" alt="生图设计后原生重建，四页两列总览" width="100%"></a><br><strong>2026-09-23 · 模板风格重建</strong><br><small>4 页 · 179 个可编辑对象 · <a href="assets/samples/v5.1-template-image-guided-4page.pptx">下载 PPTX</a></small></td>
    <td width="33%" valign="top"><a href="assets/samples/v5.1-template-native-4page-2col-overview.png"><img src="assets/samples/v5.1-template-native-4page-2col-overview.png" alt="原生模板组件复用，四页两列总览" width="100%"></a><br><strong>2026-09-23 · 原生组件复用</strong><br><small>4 页 · 61 个可编辑对象 · <a href="assets/samples/v5.1-template-native-4page.pptx">下载 PPTX</a></small></td>
    <td width="33%" valign="top"><a href="assets/samples/v5.1-no-image-policy-page-01.png"><img src="assets/samples/v5.1-no-image-policy-page-01.png" alt="v5.1 无生图政策解读封面" width="100%"></a><br><strong>2026-09-21 · v5.1 无生图封面</strong><br><small>6 页政策解读中的第 1 页 · <a href="assets/samples/v5.1-no-image-policy-native.pptx">下载 PPTX</a></small></td>
  </tr>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/v5.1-no-image-policy-page-02.png"><img src="assets/samples/v5.1-no-image-policy-page-02.png" alt="v5.1 无生图政策解读三年目标页" width="100%"></a><br><strong>2026-09-21 · v5.1 目标页</strong><br><small>同一份 6 页可编辑政策 PPT</small></td>
    <td width="33%" valign="top"><a href="assets/samples/v5.1-no-image-policy-page-06.png"><img src="assets/samples/v5.1-no-image-policy-page-06.png" alt="v5.1 无生图政策解读行动页" width="100%"></a><br><strong>2026-09-21 · v5.1 行动页</strong><br><small>同一份 6 页可编辑政策 PPT</small></td>
    <td width="33%" valign="top"><a href="assets/samples/v5.0-latin-america-ai-zh-overview.png"><img src="assets/samples/v5.0-latin-america-ai-zh-overview.png" alt="v5.0 拉美 AI 与就业研究二十页总览" width="100%"></a><br><strong>2026-09-21 · v5.0 研究解读</strong><br><small>20 页 · 447 个原生可编辑对象 · <a href="assets/samples/v5.0-latin-america-ai-zh-native.pptx">下载 PPTX</a></small></td>
  </tr>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/v5-declarative-design-native-preview.png"><img src="assets/samples/v5-declarative-design-native-preview.png" alt="v5 声明式设计原生预览" width="100%"></a><br><strong>2026-09-20 · v5 设计预览</strong><br><small>早期声明式设计示例</small></td>
    <td width="33%" valign="top"><a href="assets/samples/mgi-template-v4-31-page-contact-sheet.png"><img src="assets/samples/mgi-template-v4-31-page-contact-sheet.png" alt="V4 模板路线三十一页联系表" width="100%"></a><br><strong>2026-09-10 · V4 Template</strong><br><small>31 页研究报告演示</small></td>
    <td width="33%" valign="top"><a href="assets/samples/state-ai-2025-independent-bespoke-23-page-contact-sheet.png"><img src="assets/samples/state-ai-2025-independent-bespoke-23-page-contact-sheet.png" alt="V4 Bespoke 路线二十三页联系表" width="100%"></a><br><strong>2026-09-10 · V4 Bespoke</strong><br><small>23 页独立设计演示</small></td>
  </tr>
</table>

<details>
<summary>展开更早的 9 张示例图（2026-08 → 2026-07）</summary>

<table>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/v120-deepseek-v4-pro-state-of-ai-contact-sheet.png"><img src="assets/samples/v120-deepseek-v4-pro-state-of-ai-contact-sheet.png" alt="早期 State of AI 模型路径演示联系表" width="100%"></a><br><strong>2026-08-11 · State of AI 对照稿</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/model-path-comparison-grid.png"><img src="assets/samples/model-path-comparison-grid.png" alt="模型路径对照网格" width="100%"></a><br><strong>2026-08-11 · 模型路径对照</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/stateofai-2025-final-contact-sheet.png"><img src="assets/samples/stateofai-2025-final-contact-sheet.png" alt="早期 State of AI 演示联系表" width="100%"></a><br><strong>2026-07-21 · State of AI 演示</strong></td>
  </tr>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/ai-project-core-upgrade-contact-sheet.png"><img src="assets/samples/ai-project-core-upgrade-contact-sheet.png" alt="AI 项目核心升级示例联系表" width="100%"></a><br><strong>2026-07-21 · AI 项目升级</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/ai-project-model-routing.png"><img src="assets/samples/ai-project-model-routing.png" alt="AI 项目模型路由示意" width="100%"></a><br><strong>2026-07-21 · 模型路由</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/ai-project-agent-router.png"><img src="assets/samples/ai-project-agent-router.png" alt="AI 项目 Agent Router 示意" width="100%"></a><br><strong>2026-07-21 · Agent Router</strong></td>
  </tr>
  <tr>
    <td width="33%" valign="top"><a href="assets/samples/ai-project-execution-layer.png"><img src="assets/samples/ai-project-execution-layer.png" alt="AI 项目执行层示意" width="100%"></a><br><strong>2026-07-21 · 执行层</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/palette-upgrade-overview.png"><img src="assets/samples/palette-upgrade-overview.png" alt="早期配色升级总览" width="100%"></a><br><strong>2026-07-21 · 配色升级</strong></td>
    <td width="33%" valign="top"><a href="assets/samples/native-architecture-diagram.png"><img src="assets/samples/native-architecture-diagram.png" alt="原生架构示意图" width="100%"></a><br><strong>2026-07-21 · 原生架构</strong></td>
  </tr>
</table>

</details>

## 适用场景：三个入口

| 你要完成的事 | 输入 | 路线与结果 |
| --- | --- | --- |
| 把报告、政策文件、PRD、文章做成汇报或课程 | 源文档；可选品牌、风格参考图 | **create 资料生成**：按内容与受众设计，生成原生 PPT 和真实预览 |
| 把设计师交稿、完整幻灯片设计图还原为可编辑 PPT | 整页设计图；用于核对文字和数值的源文档 | **recreate 设计图还原**：重建对象，并对照冻结目标检查差异 |
| 使用公司或客户的 PPTX 模板，且必须保留母版或原生组件 | 原生 PPTX 模板与源材料 | **template 模板保留**：分析并复用原生组件，按模板视觉规则补充缺口 |

模板仅供风格参考、允许重新设计时使用 create；要求忠实还原已批准的整页设计图时使用 recreate。必须保留原生母版和组件时使用独立的 Template 工作流。资料页数不等于演示页数，页数预算应依据受众、目的和信息密度确定。

**设计风格不固定。** 配色、字体、构图、图表和页面节奏由当前内容、受众与品牌约束决定。复用的样式、来源索引和图标只是减少重复描述，不会强制所有页面套用同一组卡片。

**装饰商务设计与精修。** 新增可选 `decorative_business` 审核配置：逐页记录内容关系、阅读顺序、图形如何承载信息及大中小层次，整册另做构图复审。它用于发现“换了形状但布局没变”“加密后全是表格”“大图配零散文字”等问题；自动诊断仅提示复核，不评审美分数。详见[设计指南](references/decorative-business-design.md)、[页面计划表](templates/decorative-page-plan.md)和[37 页精修过程复盘](references/cases/decorative-business-refinement.md)。案例提炼自独立制作实践，不代表本项目已对该 PPT 完成端到端认证。

[经营复盘的两轮修订](references/cases/business-deck-diversity-coherence.md)进一步补充了“构图多样后失去规整”和“缺少章节与收尾”的处理：区分全册稳定的排版规范与逐页变化的主体结构，分别审核多样性、规整度和叙事完整性。`composition-check` 同时列出正文主结论对象的位置/字体和目录、章节、结束页的声明分布，帮助定位实际页图；它不自动判定布局好坏，也不要求每份简报都增加章节页。现有入口与任务字段保持兼容，旧任务无需迁移。

模板风格参考可选“参考模板图 → 生图设计稿 → 原生对象重建”；无生图工具时，模型仍可识读模板和真实预览并直接设计原生页面。两种风格参考做法都不等于继承 PPTX 母版。详见[模板风格设计与使用边界](references/template-visual-design.md)。

## 模板路线对照：保留原生组件，或参考风格重新设计

同一份拉美 AI 与就业研究报告、同一份 37 页视觉模板，选取中文封面、57% 工时技术潜力、三类国家路径、66% 技能共享四页。两稿使用相同的 42 个内容项、四页讲稿和两组图表数据。下列总览均由最终 PPTX 的实际办公软件渲染页拼成，每张图按两列展示四页；未把设计图或截图放入 PPTX 充当整页内容。

| 使用约束 | 应选流程 | 本次四页样例 |
| --- | --- | --- |
| 母版、版式、图表工作簿和指定组件必须保留 | `template`：核验模板 → 选择与克隆原生对象 → 绑定新内容 → 真实预览与编辑验收 | A 展示原生组件复用及编排 |
| 只借鉴模板风格，可重新排版；无生图工具 | `create`：读模板视觉规则 → 锁定源内容 → 原生对象设计 → 渲染预览 → 视觉修订 | 可按此流程使用；本组未单独制作第三稿 |
| 只借鉴模板风格，可使用生图工具 | `create`：锁定内容 → 生成并核对整页设计目标 → 冻结目标 → 原生重建 → 逐页对照与编辑验收 | B 展示生图设计稿后原生重建 |
| 已有批准的完整页面设计图，要求尽量还原 | `recreate`：登记目标图 → 以源文档核对文字和数据 → 原生重建与差异审核 | 设计目标由用户提供时适用；本组 B 的目标由生图工具产生 |

**A · 原生模板组件复用。** [下载四页可编辑 PPTX](assets/samples/v5.1-template-native-4page.pptx)。使用真实原生形状、图表和工作簿克隆与数据绑定能力，完成本次四页编排。**这是组件能力与视觉效果的对照样本，不是完整 strict-template 输入合同的端到端认证。**

![A：原生模板组件复用的四页 PPT 实际渲染，两列总览](assets/samples/v5.1-template-native-4page-2col-overview.png)

**B · 参考模板生图设计后原生重建。** [下载四页可编辑 PPTX](assets/samples/v5.1-template-image-guided-4page.pptx)。本例先生成四张整页设计稿，其中一张因未锁定文案被修正；再把合格设计稿作为目标，用原生文字、形状和图表重建。B 通过完整声明式构建与独立逐页审核，交付门禁为 `final_delivery_ready`、0 个阻断项。设计稿与交付稿在纹理、渐变、图标和换行上仍有差异，不能视为逐像素 1:1。

![B：模板风格生图设计并重建的四页 PPT 实际渲染，两列总览](assets/samples/v5.1-template-image-guided-4page-2col-overview.png)

| 最终 PPTX 中的对象 | A 原生模板组件复用 | B 生图后原生重建 |
| --- | ---: | ---: |
| 可编辑文本对象 | 40 | 40 |
| 原生形状、线条和路径 | 19 | 137 |
| 原生图表（各含数据工作簿） | 2 | 2 |
| 图片对象 | 0 | 0 |
| **可编辑对象合计** | **61** | **179** |

以上按实际 PPTX 的顶层对象逐个计数；图表扇区、图表内置工作簿、字符与备注不重复计数。B 多出的对象主要是可编辑几何图标与构图元素，数量增加不直接证明设计更好。两份样例都在本机 LibreOffice 中验证了修改文字、形状和图表数据后保存、重开仍可编辑；未实测其他办公软件或操作系统。这是四页同源对照，不代表所有模板都能获得同样效果。

## 没有生图模型，也能出设计预览

默认原创流程：

```text
完整源材料 → 内容与来源整理 → 结构化设计
→ 原生可编辑 PPTX → LibreOffice PDF → PNG 预览
→ 独立视觉审核与修订 → 编辑回存检查 → 最终交付
```

具备视觉理解和文本输出能力的模型，可以编写页面设计并检查程序渲染的图片；无需直接生成图片。这里会先产生内部原生候选，再得到设计预览。生图工具可选，用于独立插画或用户明确要求的外部设计目标。

| 当前能力 | 可以怎样使用 |
| --- | --- |
| 能识图，无生图工具 | 创建原创页面、还原已有设计图、检查真实预览 |
| 能识图，也能生图 | 在上述流程中按需补充独立图片素材 |
| 只有文本模型 | 可以编写结构化设计；图像理解和独立视觉验收仍需视觉模型或人工 |
| 缺少办公软件或渲染工具 | 可以准备内容与设计；补齐真实渲染后才能最终交付 |

复杂摄影和自由插画仍需要合格素材。当前声明式入口不接受任意 HTML/CSS、SVG 或模型脚本，也不承诺任意设计图都能无损拆解。可恢复数据的图表、表格使用原生数据；独立图片仅可替换，不等于内部元素可编辑。

## v5.1 实测：无生图的 6 页中文政策解读

输入为用户提供的 7 页《人工智能中小企业创业支持计划（2026—2028年）》PDF。独立作者只使用新版 Skill 和源文档完成原创稿，未调用生图工具。输出包括 6 页中文内容、逐页来源和 6 页演讲者备注；90 天行动步骤明确标为作者建议。

**下载同一份 [可编辑 PPTX](assets/samples/v5.1-no-image-policy-native.pptx)**，或查看 [对象统计与验收摘要 JSON](assets/samples/v5.1-no-image-policy-evidence.json)。以下图片均直接来自该 PPTX 的真实办公软件渲染，没有重绘或美化截图。

### 封面：13 个文本对象 + 6 个原生形状

![v5.1 无生图原创封面，主标题与三条政策主线均为原生对象](assets/samples/v5.1-no-image-policy-page-01.png)

### 目标页：16 个文本对象 + 3 个原生形状

![v5.1 三年目标页，保留“1万家以上”“突破2000家”及三个10个的原文限定](assets/samples/v5.1-no-image-policy-page-02.png)

### 行动页：18 个文本对象 + 5 个原生形状

![v5.1 原生时间轴，明确标记为作者建议而非官方申报流程](assets/samples/v5.1-no-image-policy-page-06.png)

统计直接读取交付 PPTX，每个文本框或形状计一次：

| 页码与内容 | 原生文本 | 原生形状 | 可编辑对象合计 |
| --- | ---: | ---: | ---: |
| 1 · 政策导航 | 13 | 6 | 19 |
| 2 · 三年目标 | 16 | 3 | 19 |
| 3 · 要素供给 | 15 | 4 | 19 |
| 4 · 主体培育 | 12 | 3 | 15 |
| 5 · 开源与保障 | 20 | 5 | 25 |
| 6 · 作者行动建议 | 18 | 5 | 23 |
| **全稿** | **94** | **26** | **120** |

本例图片、原生图表、原生表格和分组均为 **0**，6 页均有备注。数字是可编辑文本，不把它们称为原生图表；装饰线和圆点计入形状，备注、字符数不重复计入对象数。对象数量用于说明编辑结构，不作为设计质量分数。

该候选已通过独立逐页视觉与来源审核，门禁状态为 `final_delivery_ready`。在 **macOS + LibreOffice 26.2.4.2** 中通过 Basic/UNO 修改副本的文字、数字文字及形状颜色，保存、关闭、重开后验证修改保留、6 页备注完整，原候选文件未改变。此为实际应用对象编辑测试，并非 GUI 点击测试；不外推为 Windows/Linux 或 PowerPoint/WPS 实机验证。样例使用 Arial Unicode MS，字体未嵌入，换设备需检查字体与排版。

## v5.0 实测保留：20 页中文研究解读

输入为 67 页 *Agents, robots, and us: How AI reshapes work and skills in Latin America* 报告，输出 20 页《智能体、机器人与我们》中文研究解读，涵盖自动化潜力、经济价值、岗位与技能、国家对照和企业案例。每页均有来源与演讲者备注。这是 v5.0 阶段的真实历史成品，单独统计，不与上面的 v5.1 案例混算。

流程为“源文档 → 完整页面设计图 → 多模态识读与声明式重建 → 原生 PPTX → 实际渲染与验收”。以下保留原交付的 20 页总览图；[下载原始可编辑 PPTX](assets/samples/v5.0-latin-america-ai-zh-native.pptx)，[查看逐页对象数据](assets/samples/v5.0-latin-america-ai-zh-evidence.json)。

![v5.0 智能体、机器人与我们：20 页中文可编辑 PPT 实际渲染总览](assets/samples/v5.0-latin-america-ai-zh-overview.png)

| 对象类别 | 数量 | 可编辑范围 |
| --- | ---: | --- |
| 原生文本框 | 274 | 修改文字、字体、字号与颜色 |
| 原生形状与路径 | 164 | 移动、缩放与改色 |
| 原生图表 | 7 | 修改数据系列；附 7 个内嵌工作簿 |
| 原生表格 | 2 | 修改单元格、行列和样式 |
| **原生可编辑对象合计** | **447** | **274 + 164 + 7 + 2** |
| 独立封面图片 | 1 | 可整体替换，内部插画元素不可逐个编辑 |
| **幻灯片对象总数** | **448** | **447 个原生对象 + 1 张图片** |

统计直接读取原交付 PPTX，每个对象只计一次；图表数据点、表格单元格、7 个数据工作簿和 20 页备注不重复计数。

<details>
<summary>展开 20 页可编辑对象明细</summary>

| 页码 | 文本 | 形状/路径 | 图表 | 表格 | 原生可编辑合计 | 可替换图片 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 7 | 2 | 0 | 0 | 9 | 1 |
| 2 | 15 | 18 | 0 | 0 | 33 | 0 |
| 3 | 19 | 6 | 0 | 0 | 25 | 0 |
| 4 | 13 | 5 | 1 | 0 | 19 | 0 |
| 5 | 14 | 7 | 1 | 0 | 22 | 0 |
| 6 | 9 | 3 | 1 | 0 | 13 | 0 |
| 7 | 9 | 3 | 1 | 0 | 13 | 0 |
| 8 | 16 | 10 | 0 | 0 | 26 | 0 |
| 9 | 11 | 5 | 0 | 1 | 17 | 0 |
| 10 | 13 | 8 | 1 | 0 | 22 | 0 |
| 11 | 9 | 3 | 1 | 0 | 13 | 0 |
| 12 | 12 | 5 | 1 | 0 | 18 | 0 |
| 13 | 15 | 9 | 0 | 0 | 24 | 0 |
| 14 | 7 | 3 | 0 | 1 | 11 | 0 |
| 15 | 20 | 9 | 0 | 0 | 29 | 0 |
| 16 | 15 | 6 | 0 | 0 | 21 | 0 |
| 17 | 16 | 13 | 0 | 0 | 29 | 0 |
| 18 | 20 | 9 | 0 | 0 | 29 | 0 |
| 19 | 17 | 28 | 0 | 0 | 45 | 0 |
| 20 | 17 | 12 | 0 | 0 | 29 | 0 |
| **全稿** | **274** | **164** | **7** | **2** | **447** | **1** |

</details>

历史验收在 macOS + LibreOffice 26.2.4.2 中通过 Basic/UNO 修改副本的文字、图表数据、表格数据及图片，保存、关闭、重开后改动均保留。设计图与原生重建在字体、图标、渐变及图表样式上仍有差异，不宣称逐像素 1:1；未进行 PowerPoint/WPS 实机验证。使用的 Hiragino Sans GB、Arial 未嵌入，换设备需核对字体与排版。

## 怎么用：把目标交给 Agent

让支持读取 Skill、运行本地工具的宿主加载本目录 [SKILL.md](SKILL.md)，然后提供源材料和需求。普通用户无需手写对象 JSON。

**文档生成，无生图工具：**

```text
使用 PPT Smith，把这份 PDF 做成约 10 页中文可编辑 PPT。
受众：中小企业负责人；目标：理解政策重点并形成行动清单。
当前模型能识图，无生图工具。根据内容建议配色与页面结构，
保留数字限定词、逐页来源和演讲者备注；作者建议与原文明确区分。
完成真实预览、独立审核及目标软件编辑回存验证后交付。
```

**装饰商务汇报与精修：**

```text
使用 PPT Smith，把这份经营资料做成约 20 页中文装饰商务汇报。
启用 decorative_business 审核配置，保留原生可编辑文字、图表和表格。
先说明每页的主结论、内容关系和阅读路径，让图形组织对应的信息；
目标达成、进度、问题与改进、重要成果分别选择合适的表达。
先做代表页，确认信息密度和视觉层次，再扩展全稿。
完成真实渲染、独立逐页与整册审核、目标软件编辑回存验证后交付。
```

**根据设计图还原：**

```text
以这些完整页面设计图为还原目标，以 PDF 为文字与数字依据。
保留已批准的版式；如设计图与源文档冲突，列明需要修正的内容。
标题、正文、可恢复数据的图表和表格使用原生对象，
说明独立图片与复杂效果的编辑边界，并提供目标/实际预览对照。
```

**严格沿用原生模板：**

```text
用这个公司 PPTX 模板把报告整理成 15 页中文汇报。
母版、版式、品牌字体、原生图表及其数据工作簿必须保留。
先核验可用组件与每页内容容量，再克隆和绑定报告中的事实、数字与来源。
模板放不下时说明缺口及调整方案，附逐页讲稿，并验证编辑、保存和重开。
不要把模板截图当作幻灯片背景。
```

**模板只作风格参考，无生图工具：**

```text
参考这个 PPTX 的配色、字体层级、留白和图表语言，允许重新排版。
根据这份 PDF 做 4 页中文可编辑 PPT；先锁定各页文字、数字、单位和来源。
当前没有生图工具，请直接用原生文本、形状和图表设计页面，
渲染真实预览，逐页检查阅读顺序、品牌风格和数据标注，再修订交付。
```

**模板只作风格参考，有生图工具：**

```text
参考这个 PPTX 的视觉规则，允许重新设计；以这份 PDF 为事实依据。
先锁定 4 页中文内容、图表数据和来源，只用已核对内容生成整页设计图。
先做代表页并确认方向，再生成其余页；核对设计图中的文字、数字与可重建性。
冻结合格目标后，用原生文本、形状、图表重建可编辑 PPTX。
提供设计图与实际渲染的逐页对照、编辑保存检查和不可编辑效果说明。
```

**只修改几处内容：**

```text
基于上一份任务，只改第 6 页标题和第 7 页备注，其余保持。
用对象补丁提交改动，重新审核受影响页面；
未变页面仅通过有效审核继承机制复用记录。
```

首次说明受众、目的、语言、页数预算、目标软件，以及模板是“必须保留原生组件”还是“只作风格参考”、整页设计图是否为“精确还原目标”。后续带上原任务目录和需要修改的页/对象，Agent 可按页读取上下文，不必反复粘贴整份材料。

## 减少重复输入与返工

- **按需加载**：Skill 入口只保留公共规则，路线说明按任务读取。
- **紧凑作者输入**：样式、来源、颜色变量和装饰符号只定义一次，固定编译器展开为严格对象。
- **短摘要与分页查询**：默认返回构建状态、变更页和证据路径；详细内容按页读取。
- **真实字体预检**：在批量铺页前检查实际办公软件使用的字体与字符，结果按环境缓存。
- **版本绑定补丁与审核继承**：修改少量内容不必重写整份 JSON。备注或底层数据改变，即使预览像素相同，也会使相关审核失效。

同一份 6 页任务的实测体积如下，紧凑输入展开后与完整任务完全一致：

| 测量对象 | 原始/完整 | 优化/紧凑 | 字节减少 |
| --- | ---: | ---: | ---: |
| Skill 入口（v5.1 开发验收快照，对比 v5.0.1） | 14,384 | 6,278 | 56.4% |
| 同一任务作者输入 | 69,702 | 42,808 | 38.6% |
| 同一构建的 CLI 回显 | 24,550 | 631 | 97.4% |

单位为 UTF-8 字节；作者输入采用相同 canonical JSON 编码。[测量口径与摘要](assets/samples/v5.1-no-image-policy-evidence.json)随样例提供。**这些不是实测 token、费用或运行时间降幅。** 完整来源、原生对象、构建和审核证据仍保留。当前每次修订仍完整构建与真实渲染；继承减少重复审阅，不是页级渲染缓存。

## 安装与本地自检

在 Skill 根目录安装 Python 依赖；以下为 macOS/Linux 的 Bash 示例：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_identity.py
python scripts/quick_validate_skill.py
python -m engine design capabilities
```

真实预览与字体预检还需要 **LibreOffice、Poppler（pdftoppm、pdffonts、pdftotext）、Fontconfig（fc-match）及任务所用字体**。工具应可从 PATH 发现。Windows 使用相应虚拟环境 Python 入口；工具安装与系统差异见 [跨平台运行条件](references/declarative-design.md#跨平台运行条件)。`capabilities` 检测本地工具，不自动识别宿主模型是否能识图或生图。

以下命令展示 Agent 的创建流程，`author.json` 由模型依据源材料编写，必须位于任务目录内；`init` 本身不解析 PDF 或自动设计页面：

```bash
PPTSMITH_TASK="./ppt-work/demo"
python -m engine design init --task-dir "$PPTSMITH_TASK" --task-id demo --mode create --pages 6
python -m engine design author --task-dir "$PPTSMITH_TASK" --file author.json
python -m engine design preflight --task-dir "$PPTSMITH_TASK" --isolation auto
python -m engine design build --task-dir "$PPTSMITH_TASK" --isolation auto
```

构建成功仅产生候选。继续使用返回的构建 ID 生成审核表、完成独立审核和真实编辑检查，再执行 `review`、`deliver`。任务目录的 `state.json` 记录接续信息，`task.json`、构建 manifest 和原始审核记录保留完整证据。完整命令见 [声明式工作流](references/declarative-design.md)与 [紧凑输入/局部修订](references/declarative-authoring.md)。

只有使用依赖 PptxGenJS 的兼容构建器时，才需准备 Node/npm 并执行：

```bash
python scripts/bootstrap_pptxgenjs_runtime.py
```

该脚本在 `runtime/pptxgenjs` 内执行锁定版本的 `npm ci`。

## 交付与兼容边界

最终交付包括可编辑 PPTX、实际 PDF/PNG 预览、任务及素材记录、对象清单、审核结论和编辑限制。标题、正文、图形和可恢复的数据优先保留原生编辑能力；未经批准的整页截图不能充当可编辑成品。

PPT 质量与 OS 隔离分别验证。`--isolation auto` 在可用的 macOS 环境选择隔离模式，其他环境选择 host；host 通过质量门禁后可交付，并记录 OS 隔离未验证。显式指定 `--require-os-isolation` 时，能力不足仍阻断。运行时适配不等于所有操作系统或办公软件都已实机通过。

原生模板继续使用 [Template 工作流](references/routes/v4-template-route.md)。Bespoke 保留为高级兼容路线，Standard/Engineering 用于明确的工程草稿和诊断。`new_design`、`style_transfer` 新建参数映射到 create；已有旧任务继续遵守原来的目标要求。受限浏览器设计板、模板索引缓存和实际模型成本仪表尚未纳入本版。

## 历史样例

以下为较早版本的真实渲染样例，不计入上面的 v5.1 对象统计。

<details>
<summary>展开 V4 Template 与 Bespoke 示例</summary>

**Template：31 页研究报告演示。** 基于源报告和原生模板组件完成编排，29 个正文页具备演讲者备注。

![V4 Template 31 页实际渲染联系表](assets/samples/mgi-template-v4-31-page-contact-sheet.png)

**Bespoke：23 页独立设计演示。** 从空白页面制作，含 12 个原生图表和 23 页备注。两份样例使用不同报告，不作为同源质量比较，也不表示与源报告出版方或模板品牌存在合作、授权或背书关系。

![V4 Bespoke 23 页实际渲染联系表](assets/samples/state-ai-2025-independent-bespoke-23-page-contact-sheet.png)

更多历史资源见 [样例目录](assets/samples/)。

</details>

## 文档与分发

- [SKILL 执行规范](SKILL.md)
- [声明式工作流、原生能力与验收](references/declarative-design.md)
- [紧凑作者输入、对象补丁与审核继承](references/declarative-authoring.md)
- [Template 模板复用](references/routes/v4-template-route.md) · [Bespoke 高定兼容](references/routes/v4-bespoke-route.md)
- [V4 路线架构](references/routes/v4-three-route-architecture.md) · [历史导出能力](references/export-pipelines.md)
- [样例证据](assets/samples/v5.1-no-image-policy-evidence.json)

GitHub、ClawHub 等公开分发仅包含 Skill 运行代码、依赖声明、使用文档、模板/Schema，以及本文引用的示例与必要数据。开发测试、CI、开发笔记、推广文章、原始输入、完整验收日志、临时产物和本地工作树不进入公开版本。

本地构建和预览不自动发布文件；源材料如何传给宿主模型取决于宿主配置。飞书/Lark 云端创建、上传或分享仅在用户授权相应交付时执行。

核心引擎、通用组件、可编辑对象与 QA 以 Apache-2.0 开源。企业品牌适配、专属母版、行业生产包、定制组件与代生成/部署服务独立商业交付，不包含在公共仓库或 Skill 分发包中。
