---
name: submission-package-builder
description: Assemble a draft submission package from confirmed manuscript artifacts
  and verified venue constraints. Explicit only.
beta_workflow: bounded
---
# Submission Package Builder

## 前置输入

- 需要：manuscript、venue_assessment。
- 仅接收已获授权、已脱敏或可公开使用的材料；来源状态必须可说明。

## 执行步骤

1. 先检查门槛：pre-submission-checklist。
2. 依据已由人工核验的期刊、格式或作者材料逐项比对，不把未核验网页内容当作事实。
3. 只生成建议、草案或检查清单；将待确认项、冲突项和依据分别记录。
4. 由作者或指导者确认后才可进入下一人工环节。

## 输出与异常

- 产物：`submission_package_draft`。
- 能力说明：Assemble a draft submission package from confirmed manuscript artifacts and verified venue constraints. Explicit only.
- 输入缺失、来源未核验或门槛不满足时，输出缺失项和原因，不补造结论。

## 安全边界

- 不登录、代投、发送外部材料或替用户作出投稿/作者声明；未获人工核验的信息保持 `unknown`。
- 本 Skill 只在本地受限工作流中提供辅助，不联网核验、不读取原始数据。

## 参考

- [项目契约](../../shared/project-contract.md)
- [状态机](../../shared/state-machine.md)
