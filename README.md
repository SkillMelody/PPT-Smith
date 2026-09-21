# MeowClaw PPT Smith

<p align="center">
  <img src="assets/branding/pptsmith-github-zh.png" alt="MeowClaw PPT Smith 图标" width="836">
</p>

> English documentation: [README.en.md](./README.en.md) · OpenClaw 执行规范：[SKILL.md](./SKILL.md)

把文章、Markdown、HTML、公众号草稿、PRD、研究材料与设计说明，转成**低返工、可编辑、可验证**的专业演示文稿。

- **公开品牌：** MeowClaw PPT Smith
- **兼容安装名：** `article-html-to-ppt`、`meowclaw-decksmith`
- **兼容搜索词：** MeowClaw PPTSmith、MeowClaw 夜猫 PPT 工坊
- **当前版本：** `5.1.0-dev.1`（本地开发候选；无生图原创、紧凑作者输入和局部修订）
- **公共标识：** `meowclaw-pptsmith`
- **许可证：** `Apache-2.0`
- **开源定位：** 核心引擎、基础五风格、通用组件、可编辑对象、QA 与可信交付

> PPTSmith 的 GitHub / ClawHub 开源版用于分发、获客与建立可信度。专业生产包、企业品牌适配、专属页面原型、定制组件和代生成/部署服务采用独立商业交付，不包含在本仓库与 ClawHub 包中。

## v5.1 开发候选：三个用户入口

- **资料生成 create**：模型根据内容与受众提交结构化设计，生成原生候选 PPT 和真实 PNG 预览，视觉修订后交付；无需图片生成工具。
- **设计图还原 recreate**：读取用户提供的完整目标图，核对来源并重建可编辑对象；保留目标保真验收。
- **沿用 PPT 模板 template**：继续使用独立的原生模板组件复用路线。

工具默认输出摘要，详细证据落盘。新增样式/来源/符号引用、原子对象补丁、真实字体预检与受版本约束的分页审核继承。参见 [声明式流程](references/declarative-design.md) 与 [作者输入](references/declarative-authoring.md)。生图用于可选插图或外部设计目标；程序预览不冒充生图回执，也不以自己与自己一致证明审美通过。当前为开发候选，未发布。

## v5.0.1 声明式运行时基础

v5 将“模型直接写构建脚本”收敛为受约束的设计任务：模型提交内容、设计、场景、素材和审核记录；固定后端负责原生对象、素材边界、真实渲染和交付状态。它适用于图片复刻、参考图风格迁移和新页面设计；原生模板保留仍使用 Template 路线。

### 已验证的核心能力

1. **声明式全页场景**：原生文字、形状、曲线、图表、表格、分组和独立图片均由 JSON 合同描述；未知字段、脚本、表达式、外部 URL、SVG 载荷与路径穿越会被拒绝。
2. **内容与设计分离**：可见文字、图表数据、表格单元格、来源和备注先锁定；设计节点仅引用内容 ID，避免把业务文案藏在绘图代码里。
3. **参考图与目标图区分**：复刻、风格迁移、新设计和草稿有不同目标规则；新内容不能把旧参考图当作像素目标。
4. **素材与执行边界**：素材按哈希、页面范围、裁片和实际工具回执登记；固定 worker 限制任务 I/O、输入输出和构建时间，并用私有 LibreOffice 配置生成真实预览。macOS 隔离模式另限制文件访问与 IP 网络；host 模式不宣称具备 OS 隔离。
5. **失败关闭式交付**：构建、预览、审核、目标软件编辑检查和哈希必须匹配；候选稿不会因生成成功自动变成最终交付。

跨平台入口默认 `--isolation auto`，没有可用 macOS 隔离时采用 `host`。Linux、Windows 和 macOS 的本地 host 构建通过全部 PPT 质量门禁后均可交付，并保留“OS 隔离未验证”的记录；需要强制隔离的环境使用 `--require-os-isolation`，能力不足即阻断。依赖、字体、平台适配与验证边界见[运行说明](references/declarative-design.md#跨平台运行条件)。

### 声明式设计实际样例

下图为 `5.0.1` 开发候选的一页真实原生 PPTX 预览：设计目标保持“内容先行 → 视觉定稿 → 原生重建”的三步结构，而不是将整页设计图直接贴入 PPT。

- **实际原生对象：** 12 个可编辑文本对象 + 22 个原生形状，整页截图为 0；
- **可编辑验证：** 文本改写、图表数据替换和表格单元格改写均有自动回读测试；
- **真实预览：** macOS 隔离环境中 PPTX → LibreOffice PDF → PNG；
- **当前状态：** `candidate_unreviewed`，用于展示运行时能力，不宣称已完成正式视觉交付或跨平台编辑验收。

![PPT Smith v5 declarative design — native PPTX preview](./assets/samples/v5-declarative-design-native-preview.png)

> Alpha 边界：当前实现已完成本地开发候选与真实预览验证，但尚未完成未见参考集、PowerPoint/WPS GUI 编辑、跨环境安全审核及正式发布验收。请在受控试点中使用，不要将它视为已发布的生产承诺。

## v4.1 Beta 兼容路线

PPT Smith v4.1 Beta 是模型主导的演示创作系统。强模型负责理解来源、提炼叙事、设计页面和复核真实渲染；引擎负责来源锚定、原生对象执行、模板组件合同和失败关闭式 QA。

1. **Bespoke 高定路线**：模型从空白画布创作原生可编辑页面，追求视觉与内容上限。
2. **Template 路线**：分析用户 PPTX、建立 Component Atlas，优先复用并组合可行组件；缺失时按模板视觉语法补绘原生组件。
3. **Standard / Engineering 路线**：保留确定性编译、诊断和兼容能力，不冒充高质量最终稿。
4. **完整来源合同**：正文、数字、图表、插图和备注均可绑定来源锚点。
5. **整页设计合同**：拒绝“标题＋孤立组件”、低信息饱和度、重复骨架和占位值。
6. **原生可编辑交付**：标题、正文、图表、关系图、卡片和关键标签优先保留为 PowerPoint 原生对象。
7. **真实渲染与视觉批准**：只有绑定同一候选文件的结构检查、真实渲染和视觉复核全部通过，才能进入最终状态。
8. **失败时诚实收口**：缺少高质量 IR、模板合同、渲染器或视觉批准时明确阻断，不输出假成品。

> Beta 边界：Bespoke 与 Template 的质量依赖强模型，并要求逐任务真实渲染与人工/模型视觉复核；本版本不承诺任意模板、任意模型一次生成即可最终交付，也不承诺 Microsoft PowerPoint 与 LibreOffice 像素级一致。

### 安装与自检

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/bootstrap_pptxgenjs_runtime.py
python scripts/check_identity.py
python scripts/quick_validate_skill.py
python -m engine --help
```

开发与回归测试使用：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## 样例图库

以下样例与仓库首页保持一致，并复制到 Skill 自有资产目录，确保从当前页面浏览时可直接查看。

### v4.1.0-beta.1 Template 路线：MGI 31 页完整演示

这份样例将一份约 67 页的研究报告与用户提供的咨询风模板组合为 31 页演示稿。系统先分析模板中的可复用组件，再由模型完成整页内容编排；没有合适组件时，按模板的字体、色彩、线条、圆角和留白语法补绘原生页面。图片为同轮 LibreOffice 真实渲染联系表，不是概念稿。

- **路线：** `Template / strict component reuse`
- **输出：** 31 页；29 个正文页具备演讲备注
- **实际生成节点：** [`f14ed34`](https://github.com/SkillMelody/PPT-Smith/commit/f14ed34)（`feat(template): enforce whole-page delivery contracts`）
- **发布候选节点：** [`84e0c1e`](https://github.com/SkillMelody/PPT-Smith/commit/84e0c1e)（`v4.1.0-beta.1` 公共候选）
- **边界：** 示例用于展示 Template 路线，不代表与报告出版方或模板品牌存在合作、授权或背书关系。

![PPT Smith v4 Template route — MGI 31-page rendered contact sheet](./assets/samples/mgi-template-v4-31-page-contact-sheet.png)

### v4.1.0-beta.1 Bespoke 路线：完全独立作者 23 页演示

这份样例使用另一份研究报告，从空白 Presentation 重新设计叙事、配色、原生图表、机制图、管理框架和行动路径。测试时设置 `template=null`，没有导入 Template 作者代码、Component Atlas、模板组件或 Standard 底稿。图片为 23 页真实渲染联系表。

- **路线：** `Bespoke / independent authoring`
- **输出：** 23 页；12 个原生可编辑图表、11 个非图表页面、23 页演讲备注
- **生成与验收节点：** [`84e0c1e`](https://github.com/SkillMelody/PPT-Smith/commit/84e0c1e)（从最终 Beta ZIP 完成端到端生成与视觉批准）
- **边界：** 两张 v4 全景图使用的源报告不同，只展示路线形态，不作为同源质量优劣对比。

![PPT Smith v4 Bespoke route — independent 23-page rendered contact sheet](./assets/samples/state-ai-2025-independent-bespoke-23-page-contact-sheet.png)

### State of AI 2025：14 页完整演示样例

![State of AI 2025 14-page PPT sample](./assets/samples/stateofai-2025-final-contact-sheet.png)

### 统一配色系统升级

![Palette upgrade overview](./assets/samples/palette-upgrade-overview.png)

### 原生可编辑技术架构图

![Native editable architecture diagram](./assets/samples/native-architecture-diagram.png)

## 2.0.7 AI 工程项目汇报样例

这组样例来自真实生成并通过 LibreOffice 渲染验收的 19 页 AI 项目汇报。重点展示 2.0.7 对执行组织层、状态机、Agent Router、RAG、模型路由和部署演进的升级。

![AI engineering project core upgrade contact sheet](./assets/samples/ai-project-core-upgrade-contact-sheet.png)

### 执行组织层：跨层关系使用肘形折线

Runtime 与能力节点使用专用连接通道，避免斜直线穿越内容。

![AI project execution layer](./assets/samples/ai-project-execution-layer.png)

### Agent Router：总线代替放射式线团

Policy、Router、Dispatch Bus 与 Agent Group 分区表达，输出路径可逐条追踪。

![AI project Agent Router](./assets/samples/ai-project-agent-router.png)

### 模型路由：输入容器、策略评分与能力池

约束条件先汇入输入容器，再进入 Routing Score 和三类能力池；主路径与外部动作边界清晰。

![AI project model routing](./assets/samples/ai-project-model-routing.png)

## 适合谁

- **产品负责人 / 汇报人：** 决策摘要、指标、路线图、风险与下一步。
- **Agent 工程师 / 自动化开发者：** 工作流、架构、权限、失败模式、实施计划与 ROI。
- **自媒体作者 / 知识创作者：** 钩子、框架、案例、步骤、知识卡片与品牌节奏。
- **咨询、研究与业务团队：** 把长文、报告和证据整理成结构清晰、可追溯的正式 deck。

## 输入与输出

**常见输入**

- 文章、Markdown、HTML、微信公众号草稿
- PRD、产品方案、复盘、路线图
- 技术架构、自动化方案、Agent 工作流
- 研究材料、知识笔记、审稿通过的长文

**常见输出**

- `deck.pptx`：静态、可编辑 PPTX
- `deck-dynamic-native.pptx`：原生渐进式动态 PPTX
- `deck-preview.pdf`：在可用渲染环境下生成的预览
- `verification-report.md`：验证与限制说明
- `delivery-manifest.json`：可信交付状态与产物清单

## 快速使用

把材料、受众、目标和交付格式告诉 Agent：

```text
使用 MeowClaw PPTSmith（兼容路由 article-html-to-ppt）把这份 PRD 做成 10 页左右的可编辑 PPTX。
受众：产品管理层
目标：争取路线图审批
风格：产品汇报，克制、清晰、低返工
必须包含：关键判断、指标、路线图、风险和下一步
```

技术汇报示例：

```text
使用 MeowClaw PPTSmith 制作技术评审 PPT。
受众：Agent 工程师与业务负责人
包含：工作流、系统架构、权限边界、失败模式、实施计划和 ROI。
核心文字、表格和简单图表保持可编辑。
```

## 开发与 CI：PptxGenJS runtime

`runtime/pptxgenjs/node_modules` 是本地、被忽略的构建产物，不随 Git checkout 分发。新 clone 或新 worktree 在执行 PptxGenJS 相关测试/构建前，必须从 Skill 根目录运行：

```bash
python3 scripts/bootstrap_pptxgenjs_runtime.py
```

该命令只在 `runtime/pptxgenjs` 内执行 lockfile-pinned `npm ci`，不会全局安装、更新 lockfile 或提交 `node_modules`。CI 和排障可先用以下 preflight 获取可操作状态：

```bash
python3 scripts/bootstrap_pptxgenjs_runtime.py --check
```

## 生产链

```text
源材料 / 文章 / 设计说明
→ 内容分析与证据盘点
→ 故事线与判断式标题
→ PPT IR / Diagram IR
→ Style Contract v2
→ 能力探测与 Builder 选择
→ 组件交付路线解析
→ 可编辑 / 混合式 PPT 构建
→ 结构检查与真实渲染回读
→ 视觉评分与修订
→ 交付打包与 Delivery Manifest
```

## 五套基础视觉系统

| 风格 | 适用场景 | 默认特征 |
| --- | --- | --- |
| `consulting-light` | 管理层汇报、研究与咨询报告 | 结论先行、留白克制、证据清晰 |
| `product-report` | PRD、路线图、发布与复盘 | 指标、权衡、计划与产品节奏 |
| `technical-blueprint` | 架构、工作流、实施与运维 | 精确边界、节点、链路和故障模式 |
| `consulting-blueprint-hybrid` | Agent / 自动化的业务技术汇报 | 咨询结构为主，技术图解为证据层 |
| `editorial-knowledge` | 长文、课程、知识产品与个人 IP | 温暖纸张感、框架化、便于传播 |

这些是公开基础系统。企业品牌模板、专属母版、行业生产包和定制组件不随开源包发布。

## 可信交付边界

PPTSmith 不把“文件生成成功”等同于“最终完成”：

- **Created**：PPTX 已生成。
- **Rendered**：真实办公套件或渲染器已完成渲染。
- **Read back**：结构与渲染结果已回读检查。
- **Verified**：合同、结构、QA 与证据通过验证。
- **Final**：满足对应生产档位的全部可信门槛。

v5.0.1 的声明式设计运行时已在开发候选环境完成 768 项全量回归（16 项跳过）及 41 项最终路线回归；真实预览样例包含 12 个原生文本与 22 个原生形状。该证据不等于对所有参考图、Microsoft PowerPoint、WPS、模型或用户模板的生产承诺。

## 隐私与云端导出

敏感草稿、内部 PRD、业务指标和未公开材料默认优先本地生成 PPTX。只有用户明确要求并确认目标位置与分享边界后，才进入飞书 / Lark 云端创建或上传流程。

## 文档入口

- [OpenClaw 执行规范](./SKILL.md)
- [V5 声明式设计工作流](references/declarative-design.md)
- [V4 三路线架构与执行隔离](references/routes/v4-three-route-architecture.md)
- [V4 Bespoke 高定路线](references/routes/v4-bespoke-route.md)
- [V4 Template / Path C 路线](references/routes/v4-template-route.md)
- [V4 Template 通用化约束](references/routes/v4-template-generalization.md)
- [旧版本迁移指南](references/migration-v1.1-to-v1.2.md)
- [英文 README](./README.en.md)
- [生产配置说明](references/production-profiles.md)
- [组件交付与 Builder 适配](references/builder-adapters.md)
- [验证体系](references/verification-harness.md)

## 开源与商业化边界

本仓库与 ClawHub 包持续开放可复用的 PPTSmith 核心能力，让个人与团队能独立生成、检查并交付可靠的演示文稿。

以下内容保持独立商业交付：

- 专业生产包与行业化工作流
- 企业品牌适配、专属母版与视觉资产
- 专属页面原型与定制组件
- 代生成、部署、培训、维护与私有化服务

这样既不削弱开源版的真实可用性，也避免把高价值商业资产混入 Apache-2.0 公共分发包。公共发布树不包含任何私有生产包源文件。
