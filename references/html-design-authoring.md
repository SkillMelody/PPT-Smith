# HTML 设计面 → 原生对象（`html-import`）

`create` 的逐页设计可以写成受限 HTML/CSS，再由固定工具编译为现有场景记录。
浏览器提供真实的网格/弹性布局与文字测量，模型无需手算绝对坐标；
编译结果仍是 `task.json` 中的 text/shape/path/table/chart 节点与内容记录，
`validate`、字体预检、构建、渲染、独立审核与交付门禁完全不变。HTML 不进入 PPTX，
任务中的脚本从不执行：页面里出现 `<script>` 会被拒绝，提取器由工具自带并注入。

适用：逐页稿、文档转演示、信息密集页、需要明确主次的商务页。图片重建仍走 recreate，
原生模板改页仍走 template。HTML 预览是作者自己的草图，**不得**登记为外部设计目标或 recreate 目标。

## 流程

1. 读原文，写 `page-plan.md`（见 [逐页稿合同](outline-to-deck.md)），先完成内容重构：
   定主视觉与首要信息；同一组数据只编码一次（图与同数表合并，数值直接标在图上）；
   按读者问题而非原稿编号分组；限定、口径和来源仍然上屏。
2. 为整册定一套主题：画布、字号层级、颜色角色、间距、卡片与表格样式。各页复用主题，
   正文构图随内容关系变化。
3. 每页写一个 HTML 文件（任务目录内），然后导入：

```bash
python3 -m engine design html-import --task-dir "$TASK" --page page-2 --file pages/p06.html \
  --source-file user-input.md --source-heading 第06页
```

4. 打开返回的 `preview`（浏览器截图），修改 HTML 并重复导入，直到版面成立。
   截图只用于迭代；验收以构建后的真实 PPTX 预览为准。
5. 用 `author`/`patch` 填写 `design.brief`、各页 `composition`（`reading_path` 引用导入后的内容 ID）
   和备注，然后 `validate --complete` → `preflight` → `build` → 独立审核 → `deliver`。

导入只替换该页的场景与内容记录。`composition` 引用的 ID 若已不存在，会被移除并在结果中
标记 `composition_reset: true`，需重新填写。给关键元素设置稳定的 `data-cid` 可避免这种情况。

## 画布与结构

- 恰好一个 `id="slide"` 的根元素，尺寸等于任务画布，**1 CSS px = 1 pt**（如 1440×810 或 960×540）。
- 推荐：根元素 `position:relative`，大区块绝对定位，区块内部用 flex/grid 流式排版。
  长度不确定的文字放在流式容器里，不要用固定 `top` 逐行摆放。
- 每个文字块是一个元素；同一句内的样式变化用内联 `span`/`b`。不要在同一元素中
  混排文字与块级子元素。单行标签加 `white-space:nowrap`，防止目标软件换行不同。

## 支持与不支持

| 可用 | 编译为 |
| --- | --- |
| `background-color`（可带 rgba 透明度）、`border`、统一 `border-radius` | 矩形/圆角矩形；单边边框为独立细矩形 |
| 文字：`font`、`color`、`line-height`、`letter-spacing`、`text-align`、`padding` | 原生文本框；内联样式为 spans；精确行高 |
| `<table>`（无 colspan/rowspan）：单元格底色、字体、对齐、内边距、下边框 | 原生表格，逐格样式，无主题表格样式 |
| `<svg data-native-svg>` 内的 `<path>`（绝对 M/L/Q/C/Z，`fill-opacity`、`stroke`） | 自由曲线（流带、箭头、图形） |
| 带 `data-chart` 的元素 | 原生图表（数据可编辑） |

不支持：`img`/`script`/`iframe`/表单/链接、`url()`、`@import`、`@font-face`、事件属性、
`svg <use>`。渐变、背景图、`transform`、竖排在报告中给出警告；阴影被忽略；
`opacity` 请改用 rgba；不对称圆角会变直角；`::before/::after` 的文字与列表符号不会被提取，
需要的符号请写成真实文字。导入结果的 `browser_warnings`、`conversion_notes` 必须处理或说明。

## 数据属性

| 属性 | 用途 |
| --- | --- |
| `data-cid="p6-title"` | 指定内容 ID（`composition.reading_path`、`claim_content_id` 引用） |
| `data-src="user-input.md / page-6 / block-3"` | 该元素及子元素的来源定位；缺省用 `--default-source` 或源文件+标题 |
| `data-authored` | 模型撰写的措辞（标题提炼、标签、单位说明、主数字组合、页码等）；依据记入 `page-plan.md` |
| `data-native-svg` | 该 `<svg>` 的 `<path>` 编译为原生形状；未标记的 SVG 会被忽略并警告 |
| `data-chart='{...}'` | 原生图表规格，见下 |

图表规格（预览可在元素内自绘 SVG，编译时以规格为准）：

```json
{"type": "line", "categories": ["1月", "2月"], "min": 75, "max": 100, "major": 5,
 "series": [{"name": "准时足量到货率（%）", "values": [82, 85], "color": "4B4FD6", "area": true}],
 "labels": true, "markers": true, "font": "Inter"}
```

`type` 为 `line`/`column`/`bar`；`area` 为折线下浅色面积；省略 `font` 时使用本页主要字体。
截断纵轴必须在页面上说明，并保留原稿刻度。

## 追溯与覆盖

`--source-file`（可配 `--source-heading` 截取该页）启用两个方向的检查：

- **上屏 → 原文**：文字、表格单元格、图表分类与数值逐项在原文中查找（忽略空白与 `·→⇄⚠` 等装饰符）。
  找到即 `checked: true`；`data-authored` 记录为已核对并附不确定说明。其余记录返回
  `untraced_content`，**任务不变**：修正措辞，或确认属于有意撰写后加 `data-authored`。
- **原文 → 上屏**：报告未出现的数字与短语。数字缺失必须处理；短语缺失多为拆分标签或改写表头，
  逐条判断，确有遗漏就补上屏。没有源文件时只能用 `--assume-checked` 声明已人工核对。

## 字体

`font-family` 写成“拉丁字体, 中文字体”栈（如 `'Inter','Noto Sans CJK SC'`），编译时自动设置
`ea_family`。只用本机已安装、目标软件可用的字体；不要依赖网页字体。符号（⇄ → ✓ ⚠ ₂）放在
确认含该字形的字体中，`preflight` 会按实际使用的字体逐个字形核对。

## 设计方法（可迁移手法，不是固定模板）

- **入口**：每页一个最先被看见的东西（主数字、主关系图、深色主视觉区），尺寸和位置拉开层级；
  字号至少分 4–5 级，主数字远大于正文。
- **按指标/对象聚合**：定义、公式、口径、趋势、明细放在同一列或同一卡片，避免跨区查找。
- **关系用结构表达**：流程用箭头带，制衡用 ⇄ 成对，因果用 原因→机制→结果→影响 行；
  不为凑图形把并列画成因果。
- **语义色**：同一状态/指标在流带、表头、标签、强调条上同色；正文色和提示色固定。
- **浅表格**：无竖线、细横线、关键行底色高亮，数值右对齐，单位并入表头或标题。
- **限定醒目**：口径警示、截断坐标、待核实数据用固定提示样式放在相关位置或页脚。

每次任务按当前内容、受众与参考重新选择配色和构图，不沿用上一任务的品牌或版式。

## 已知差异

- LibreOffice 会在中文与西文/数字之间自动加间距；PowerPoint/WPS 需实机检查。
- 原生图表由图表引擎重绘，外观按规格近似预览；表格行高在目标软件中可能随字体度量增高。
- 浏览器截图与 PPTX 渲染不同源：两者都要看，但只有 PPTX 渲染是交付证据。
