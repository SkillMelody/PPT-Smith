# PPTSmith v4 评估：v3 差异 / 发布就绪度 / 后续规划

> 评估时间：2026-08-18 · 评估基线：v4 = `PPT-Smith` @ `23e619a`（4.1.0-alpha，工作区干净，330 单测通过）；v3 = `MeowClawLab/Skills/article-html-to-ppt` @ v3.0.0
> 结论速览：v4 是 v3 的**架构级重构**（不是增量），核心价值已达成；**值得发布**，但发布前需补齐「发布层」三件事（文档同步 / 真实模型 IR 基准 / 名称版本统一）。

---

## 1. v3 与 v4 的本质差异

| 维度 | v3.0.0 | v4.1.0-alpha | 性质 |
|---|---|---|---|
| 生成协议 | 双路径：Path A（LLM 写代码）+ Path B（IR/Pipeline 多合约） | 单路径：模型只写**内容 IR**，一次 `compile` 命令完成全部视觉 | **架构重构** |
| 视觉决策归属 | 分散在 Style Contract + 组件路由 + 模型辅助 | **纯规则引擎**（`engine/policy.py` 选 archetype，置信度兜底） | 引擎化 |
| 模型职责 | 多（写代码 / 写 IR / 视觉判断） | 单（写内容，可跳过，引擎抽取兜底） | 收敛 |
| 模型能力依赖 | 高（Path A 质量=模型编码能力） | 低（弱模型也能出保底，强模型靠 IR 丰富度提上限） | 降门槛 |
| 合约数 | 23 个 schema / 34 脚本 | 核心 1 个 `presentation-ir.schema.json` + style pack | 简化 |
| 图表/图解 | Diagram IR + 组件注册表 + SVG/原生混合 | `chart` / `diagram_ir` 原生直出（column/bar/line/pie/combo + 5 类图解） | 原生化 |
| 自动化程度 | 多命令管线 + 人工复核 | 单命令 + 自动修复循环（max 3）+ 诚实降级 | 提效 |
| 质量评估 | 6 维 rubric + golden anchor（15/18 证据） | **同一套** 6 维 rubric + golden anchor（`score_v4` 复用 `score_deck`） | 可对比 |
| 确定性 | 管线步骤多，部分依赖模型 | 编译产物确定性（benchmark 验证：同输入同几何） | 提升 |

**一句话**：v3 是「给模型的完整工具箱 + 信任模型使用」，v4 是「模型只负责内容判断，视觉能力全部收进可验证的本地引擎」。

## 2. v4 相对 v3 的具体提升（已实测验证）

1. **模型门槛下降，天花板保留**：
   - 弱模型：不写 IR，引擎抽取兜底，`ir_origin: extractive`，benchmark 实测走通率 100%、0 空白页、0 QA 错误。
   - 强模型：写 IR 丰富度（metrics/relations/message/chart/diagram_ir），引擎据此选更优 archetype（L1/L2 tier 由行为探针授予）。
   - 实测：14 页真实文档（McKinsey State of AI 2025）13/13 章节覆盖，0 QA 错误，仅字体降级。
2. **视觉能力确定性**：同样输入产出同样几何（benchmark 几何确定性 ✅），这直接支撑「低返工」和「可回归」。
3. **原生可编辑性增强**：step_cards、heat_matrix、phase_roadmap、layered_architecture、drill_down_stair、causal_chain、原生图表、双色页脚——均为 PowerPoint 原生对象（QA 阻断越界/空白/不可编辑）。
4. **诚实交付制度化**：`--no-degrade` 失败→修复循环→抽取兜底，`compile-result.json` 明确记录 `ir_origin`/`degradations`/`coverage`，不伪造 verified。
5. **工程可测性**：330 单测全绿；`benchmark_v4.py` 把 v3 的 P8 验收口径（走通率/空白页/QA/降级/覆盖率/确定性）变成一键可跑。

## 3. 是否值得发布：**值得，但分两层**

### 3.1 引擎层（可发布）
- 单命令、确定性、诚实降级、双 builder、5 套风格、原生图表、6 维 rubric 对齐 v3——**核心价值已达成且可验证**。
- 真实文档冒烟（本篇上文）+ 330 单测 + benchmark 全绿 = 引擎层具备发布条件。

### 3.2 发布层（当前缺失，是「值得发布」的真正前置条件）
| 缺口 | 现状 | 影响 |
|---|---|---|
| README.md / skill-card.md / docs 仍是 v3 文案 | 当前版本标注 3.0.0，通篇 Path A/B 双路径 | 用户/Agent 看到的是 v3 的旧承诺，与 v4 协议冲突 |
| 无 v4 发布说明/验收报告 | docs/ 只有 v2/v3 时代文档 | 无法向用户/下游证明 v4 相对 v3 的改进与验收证据 |
| 无真实模型产出的 v4 IR 基准 | v4-bench irs/ 只有 sim-* 模拟 | 缺少「多模型 × v4 引擎」的真实质量证据（v3 有 model-path 对比表） |
| 版本号/名称未统一 | SKILL.md=4.1.0-alpha，README=3.0.0，skill-card=3.0.0 | 品牌与版本混乱，违背「MeowClaw PPT Smith」定位 |

**结论**：v4 引擎值得发布；但**先发布"发布层"再对外**——补齐上表 4 项，即可从 `4.1.0-alpha` 升为正式版。

## 4. 后续规划：对齐「用户 DIY 自己的设计感 + 不碰图表代码」终极目标

v4 引擎已为这个目标搭好地基：**style pack 是可校验的结构化数据包**（colors/typography/grid/spacing 全参数化），engine 是确定性规则，模型只写内容 IR。这三点恰好把「用户的设计感」和「用户的实现」分离。

### 阶段 P9 — 用户风格模板（DIY 的入口）【发布后第一优先】
- **Style Pack 编辑器/模板化**：把 `styles/*.json` 升级为「用户模板」一级公民：提供 `template-pack` 规范 + 从用户 PPTX 提取配色/字体/版式的引导脚本（v3 已有 `template-pack.schema.json`，v4 需对齐）。
- **模版锁定与校验**：用户上传自己的模板→引擎生成可校验 style pack→QA 保证"长在用户模板里"。
- 交付物：`docs/template-authoring-guide.md` + `scripts/template_from_pptx.py` + 示例模板库。

### 阶段 P10 — 图表/图解零代码（用户不用管图表代码）【核心承诺】
- v4.1 已有原生 chart/diagram_ir。下一步：
  - **从文本/表格自动推断图表**（如 metric 块→自动选 column/bar；relation=comparison→combo）——模型不写 chart 结构，引擎推断。
  - 图表样式并入 style pack（用户模板决定图表配色/字体，不写代码）。
- 交付物：chart 推断规则 + 图表风格并入模板 + 黄金锚定验证。

### 阶段 P11 — 设计感上限（已完成）
- L1/L2 autonomy 已启用：L1 从引擎候选菜单选 archetype（`autonomy_l1`）；L2 网格行结构提案（`proposed_grid`），QA 门禁兜底，被拒提案诚实记录并回退规则。
- 本地硬化飞轮已验证：L2 通过提案 → 内容无关模式（角色签名+行结构）存储 → 同构 slide 匹配并实例化。
- 交付物：`engine/proposal_apply.py` + `layout._layout_proposed_grid` + IR schema `proposal` 字段 + 11 测试。

### 阶段 P12 — 可信交付与多模型基准
- 用真实模型（DeepSeek/GLM/MiniMax 等）产出 v4 IR，填充 v4-bench，形成多模型 × v4 的验收报告（对齐 v3 的 model-path 对比表）。
- 交付物：`docs/v4.0.0-release-notes.md` + 验收报告 + 黄金锚定基准。

### 阶段 P13 — 商业化分层（对齐 v3 开源/商业分界）
- 开源：核心引擎 + 5 套基础风格 + 模板编辑器骨架。
- 商业：企业品牌模板包、专属组件、代生成/部署（v3 已有 `private-pmo-pack`，v4 需对齐）。

## 5. 落地清单（建议顺序）

1. **立即**（发布前置）：更新 README.md / skill-card.md 到 v4；写 `docs/v4.0.0-release-notes.md`；统一版本号。
2. **P9**（已完成）：style pack 用户模板化 + 从 PPTX 提取模板的引导脚本。
3. **P10**（已完成）：图表自动推断（文本/表格→chart）+ 图表风格并入模板。
4. **P11**（已完成）：L1/L2 autonomy 激活 + 本地硬化。
5. **P12**：真实模型多模型 v4 基准 + 验收报告。
6. **P13**：商业化分层。

> 每阶段以「可验证交付」收口：引擎确定性（benchmark）+ 6 维 rubric 黄金锚定（与 v3 同源，可比）。
