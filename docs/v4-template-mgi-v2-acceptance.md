# V4 Template MGI v2 验收

## 范围

本轮使用通用背景语义、组件适配、最低内容密度、系列规划和真实渲染指纹重新编排 MGI。
旧 41 页文件保留为失败回归样本；本轮使用独立输出目录，不覆盖旧证据。

## 叙事与页面变化

- 总页数从 41 页缩减为 31 页；
- 保留 24 页区域主叙事；
- 五国 15 页重复“三件套”压缩为 5 页跨国综合比较；
- 新五国系列依次表达技术潜力、价值集中、共享技能、AI fluency 增速和 Skill Change Index；
- 五页分别使用 benchmark columns、ranked bars、shared-skill trend、full-width fluency trend 和 radar diagnostic；
- 第 2、21、22 页不再继承整行灰色源页底板，改为具有独立边界的模板语法卡片；
- 圆环图使用明确的模板主题扇区色；
- 第 17 页增加强调证据块，消除空白率问题；
- 第 11、14 页解释卡与图表区域完全分离。

## 机器与视觉门禁

- 31/31 页真实渲染通过；
- 29/29 正文页 speaker notes 通过；
- 14 个原生可编辑图表；
- 内容绑定、来源覆盖、组件意图、Atlas、资产保真和字号门禁通过；
- 结构新增问题为 0；
- 29 个正文页识别出 18 种真实渲染布局；
- 最大布局聚类 3 页，无连续三页同一骨架；
- 五国系列 5 页具有 5 种主视觉；
- 10 个存在可行模板组件的页面中复用 9 页；另 1 页具有完整不适配理由并使用模板风格原生组件；
- PPTX 与真实渲染报告完成双哈希视觉批准。

运行时状态：`final_delivery_ready`。该状态表示工程和本轮逐页视觉复核完成，仍接受用户
进一步人工评审。

## 交付物

运行目录：

`test-runs/mgi-model-directed-20260908-v2/`

主 PPTX：

`mgi-model-directed-template-v2-final.pptx`

验收记录：

- `strict-report.json`
- `visual-review.json`
- `final-approval.json`
- `qa/candidate/contact-sheets/`

## 回归

```text
720 passed, 16 skipped, 0 failed in 852.42s
```

16项跳过为仓库既有外部环境/真实模板夹具；Template通用矩阵和本轮新增指纹测试均已执行。
