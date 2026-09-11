# v0.2 Beta 脱敏试跑报告模板

> 初始状态：`not_started`。本模板不是实际试跑记录；只在按 [试跑协议](beta-pilot-protocol.md) 完成授权、脱敏和人工确认后填写。机器可复核的 YAML 证据必须由 `scripts/pilot_audit.py` 生成；本页只作为其公开说明摘要。

## 基本信息

- 报告状态：`not_started | in_progress | completed_limited | blocked`
- 插件版本与 commit：
- 试跑日期（可只保留年月）：
- 支持 Profile：`zh-undergrad-information-management-empirical`
- 授权与脱敏确认：`confirmed | not_confirmed`
- 公开材料范围：只含 artifact ID、状态、哈希/命令结果和本模板中列出的摘要。

不得填写真实题目、姓名、学号、联系方式、原始资料、全文、未授权文献内容或外部系统凭据。

## 路径记录

| 步骤 | artifact ID / 状态 | 契约校验命令与结果 | 人工确认 | 阻塞或偏差 |
| --- | --- | --- | --- | --- |
| 约束采集 | 待填写 | 待填写 | 待填写 | 待填写 |
| Context Brief | 待填写 | 待填写 | 待填写 | 待填写 |
| Timeline Baseline | 待填写 | 待填写 | 待填写 | 待填写 |
| 本地文献与 Gap Card | 待填写 | 待填写 | 待填写 | 待填写 |
| Review Board | 待填写 | 待填写 | 待填写 | 待填写 |

## 可复核摘要

- 最终项目状态：
- 已执行的本地校验命令与退出状态：
- 人工确认 artifact ID 与确认时间（可按月脱敏）：
- 未核验、`blocked`、`PIVOT` 或 `KILL` 的项目：
- 未纳入本次试跑的能力：

## 限制与结论

建议固定表述：

> 本报告记录一次在已授权、已脱敏边界内完成的受限流程验证。它验证的是所列本地 artifact、状态转换和人工确认的可追溯性；它不构成研究结论、来源真实性保证、模型效果担保、逐项功能测试完成或投稿验证。
