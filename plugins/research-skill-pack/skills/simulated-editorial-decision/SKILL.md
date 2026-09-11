---
name: simulated-editorial-decision
description: Produce a clearly simulated editorial assessment from completed reviewer
  findings. Explicit only.
beta_workflow: bounded
---
# Simulated Editorial Decision

## 前置输入

- 需要：review_reports、manuscript_state。
- 仅接收已获授权、已脱敏或可公开使用的材料；来源状态必须可说明。

## 执行步骤

1. 先检查门槛：review-report-present。
2. 针对已提供的论证、方法、评审意见或版本材料逐项审阅，并将判断关联到可追溯证据。
3. 把发现分为可修改建议、证据不足和需要人工裁决三类，不将模拟意见表述为真实决定。
4. 在人工确认修改优先级后，输出可复核的下一步。

## 输出与异常

- 产物：`simulated_editorial_decision`。
- 能力说明：Produce a clearly simulated editorial assessment from completed reviewer findings. Explicit only.
- 输入缺失、来源未核验或门槛不满足时，输出缺失项和原因，不补造结论。

## 安全边界

- 不替代同行评审、统计复核或编辑决定；证据不足时保留 `unknown`、`blocked` 或 `advisory_only` 状态。
- 本 Skill 只在本地受限工作流中提供辅助，不联网核验、不读取原始数据。

## 参考

- [项目契约](../../shared/project-contract.md)
- [状态机](../../shared/state-machine.md)
