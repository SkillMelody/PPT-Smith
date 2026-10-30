# PPT Smith

- **版本**：5.3.0
- **安装标识**：`article-html-to-ppt`
- **公开标识**：`meowclaw-pptsmith`
- **兼容别名**：`article-html-to-ppt`、`meowclaw-decksmith`
- **作者**：SkillMelody / MeowClaw Lab
- **许可证**：Apache-2.0

## 用途

把源文档、完整幻灯片设计图或原生 PPTX 模板，转为有来源、可修改并具有真实预览的演示文稿。宿主 Agent 负责内容理解、叙事和逐页设计；固定工具执行原生对象操作、渲染与证据核验。普通用户不必手写 JSON。

## 三种入口

| 需求 | 路线 | 结果 |
| --- | --- | --- |
| 从报告、政策、PRD、文章或数据制作新演示 | `create` | 原生文字、形状及支持的数据图表，配合真实预览与独立审核 |
| 根据批准的完整页面设计图重建 | `recreate` | 可编辑对象，以及目标与实际页面的差异说明 |
| 保留 PPTX 原页、母版、布局及原生组件 | `template` | 原页克隆与原生编辑；已有 Atlas/组件任务保持原合同 |

## 5.3.0 更新

- 新增 `python3 -m engine template` 固定工具链：检查实际源页与对象、克隆原页、编辑文字/原生图表/表格、同源样式继承、增删排序与备注。
- 修订使用稳定页 ID 和 revision 事务；失败不提交部分结果，冻结模板支持后续继续编辑。
- 导出后进行真实渲染、源资产保留检查、装饰/字号底线核验，以及与当前文件和逐页图片哈希绑定的外部审核。
- 不将网站的建议性视觉审核策略用于 Skill 正式交付；没有实际渲染或有效审核就不冒称终稿。
- README 新增用户提供的 36 页小米经营复盘模板路线成稿展示；总览来自真实 PPTX 渲染，不是重新绘制的宣传示意图。

## 能力边界

新原页执行器要求 POSIX `fcntl` 和 `O_NOFOLLOW`，本机 macOS 验证，Windows 不支持；源模板和输出各最多 100 页。原生图表编辑限单 plot 类别图，表格不改变行列或合并结构；图片新增仅复制同源嵌入图片。复杂效果及不支持的对象操作须明确报告，不能静默栅格化冒充原生编辑。

可编辑对象存在不等于目标办公软件兼容；LibreOffice 渲染不等于 PowerPoint/WPS GUI 编辑、保存和重开通过。模型能力、字体、渲染器与源资料会影响实际结果。工具不自动核实经营或科研事实，不认证审核者身份，也不自动继承新候选的旧审核。

## 交付与隐私

正式交付需包含可编辑 PPTX、实际预览、来源/缺项、审核结论及编辑限制。来源不明的数字保持待核实，推断与原文事实分开，不用整页截图伪装可编辑重建。渲染与文件操作在本地完成；资料如何进入模型由宿主配置决定。云端创建、上传与分享须有相应授权。

## 文档

- [Skill 执行规范](SKILL.md)
- [原页编辑式模板流程](references/native-template-workflow.md)
- [已有模板组件流程](references/routes/v4-template-route.md)
- [声明式设计与验收](references/declarative-design.md)
- [紧凑输入与局部修订](references/declarative-authoring.md)
- [装饰商务设计](references/decorative-business-design.md)
- [版本与分发范围](references/BUNDLE-MANIFEST.md)
