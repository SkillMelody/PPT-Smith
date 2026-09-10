# V4 Template 通用化基础能力验收

## 结论

本阶段通过。V4 Template 已将单一麦肯锡模板暴露的背景污染、机械缩放、内容不足和
布局伪多样性问题，转换为模板无关的 Atlas、编排和真实渲染门禁。Bespoke 与 Standard
未导入这些模块。

本阶段不等于 MGI 新稿通过。旧 41 页 MGI 文件经新门禁重审后失败，需重新编排。

## 已实现

### Component Atlas 适配合同

`engine/template_component_adaptation.py` 从当前上传模板的 reviewed 对象角色与标准化几何
动态生成：

- `content_bbox` 与 `decoration_bbox`；
- 背景对象、面积比及 `strip_on_reuse` / `reflow_to_content` / `retain_component`；
- 原生和支持宽高比；
- `scale_uniform`、卡片重排、文本容器、图表绘图区和背景重排能力；
- 最低信息单元、最低标签字符和最低数字标注；
- 组件的系列页面角色。

大于内容边界的页面/行背景不再默认进入复用组件。组件要求铺满目标区域但宽高比超出
能力时会 fail-close；普通 `contain` 仍保留兼容行为并输出适配警告。

### 页面内容密度

Template 页面构成检查现在同时验证组件自身的最低信息量和必需 companion。大容量组件
只有少量短文案时，不能再仅凭“没有溢出”通过。

### 真实渲染指纹

`engine/template_visual_fingerprint.py` 从真实渲染 PNG 提取空间占用指纹。颜色不参与布局
身份，左右镜像视为同一视觉骨架，因此 recipe 改名、图表左右翻转不能伪造页面多样性。

### 系列规划

`engine/template_series_planner.py` 要求比较系列声明统一锚点和尺度；主叙事中的单一系列
最多五页，超出时建议合并为小多图或移至附录。非比较系列不能连续重复同一主视觉。

### 品牌硬编码清理

旧确定性 manuscript planner 中按 `mckinsey.*` 组件 ID 和源模板形状名称分解仪表盘的
生产逻辑已移除。模板专属 ID 仅保留在其真实回归测试数据中。

## 跨模板矩阵

动态生成并验证：

- 明亮咨询风 16:9；
- 深色科技风 16:9；
- 极简商务风 4:3；
- 图表密集模板；
- 图片主导模板；
- 中文政企汇报模板；
- 未知 vendor/组件 ID 的保留模板。

所有样本通过同一 `analyze_template → build_component_atlas → build_component_plan` 路径，
没有模板名、品牌色、页码或组件 ID 分支。

## MGI 历史稿重审

旧 41 页 MGI 的 39 个正文页被识别为 7 类真实视觉骨架；其中 27 页属于同一骨架，且
第 11–13 页连续重复。因此触发：

- `TEMPLATE_RENDERED_LAYOUT_CONSECUTIVE_LIMIT`；
- `TEMPLATE_RENDERED_LAYOUT_OVERUSED`。

原 `final_delivery_ready` 结论已在 MGI 验收文档中标记为历史状态，不再有效。

## 测试

专项测试：

```text
116 passed, 0 failed
```

全量仓库回归：

```text
719 passed, 16 skipped, 0 failed in 901.04s
```

16 项跳过为既有外部环境/真实模板夹具；仓库内跨模板矩阵不依赖这些外部夹具。

## 下一阶段

使用新合同重新规划 MGI：减少重复图表＋侧栏骨架，合并五国系列，按真实信息关系使用
小多图、热力图、矩阵、机制图和独立深度页，再进行逐页人工视觉验收。
