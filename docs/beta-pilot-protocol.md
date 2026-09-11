# v0.2 Beta 匿名真实试跑协议

本协议用于把一次真实但受限的使用过程变成可复核证据。它不是研究结论、期刊投稿验证或对模型能力的担保。

## 隐私与授权前提

1. 仅使用参与者明确授权的匿名真实选题约束、公开资料或已获授权的本地文献元数据。
2. 真实项目必须位于仓库外的独立本地目录；不得提交题目、姓名、学号、联系方式、原始数据、访谈文本、全文、Cookie、密钥或未获授权的文献内容。
3. 任何疑似敏感内容、授权不清内容或需要联网核验的判断，均停在 `blocked` 或 `unknown`，不以推测补齐。
4. 公开时只填写脱敏报告模板；可公开材料只保留 artifact ID、状态、哈希/命令结果、人工确认与偏差说明。

建议将独立试跑目录命名为 `research-skill-pack-beta-pilot-private`，并确保它不在本仓库中。

## 受限试跑路径

开始前记录插件 commit、日期、操作环境和唯一支持的 Profile：`zh-undergrad-information-management-empirical`。

1. **约束采集**：由用户提供已授权的研究类型、时间、导师/课程约束和可用资源；记录缺失项，不记录身份信息。
2. **Context Brief 确认**：生成 `context_brief`，由用户人工确认；记录 artifact ID、确认时间和未确认限制。
3. **Timeline Baseline**：建立 `timeline_baseline` 或 `execution_timeline`，由用户确认；运行项目契约校验并保存命令结果。
4. **本地文献与 Gap Card**：仅导入可公开或已授权的文献元数据/定位信息；生成 `gap_card`，把未核验来源标为 `unknown`。
5. **Review Board**：运行 `research-review-board` 并产生 `board_decision`；用户人工确认、PIVOT、KILL 或阻塞均是有效结果，不能为了“跑通”改写为 GO。
6. **结尾校验**：再次执行项目契约校验，确认每个状态转换和人工确认都有对应 artifact；将偏差、失败和未做步骤写入报告。

每一步均应记录：输入类别（不记录敏感内容）、artifact ID、状态、依赖、校验命令及其退出状态、人工确认点、阻塞/偏差。

## 最低通过条件

- 至少一次 Context Brief 或 Timeline 的明确人工确认。
- 每个完成的状态转换均通过项目契约校验；出现校验失败时保留失败记录并停止推进。
- 最终报告使用 [脱敏试跑报告模板](beta-pilot-report-template.md)，明确写为“一次受限流程验证”。

未满足以上条件时，报告状态只能是 `not_started`、`in_progress` 或 `blocked`，不得称为“真实试跑完成”。
