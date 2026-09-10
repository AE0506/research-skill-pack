---
name: manual-rewrite-queue-builder
description: Turn originality, substance, and traceability findings into a prioritized human rewrite queue. Use explicitly after audits.
---

# Manual Rewrite Queue Builder

把审计结果转为用户可执行的人工补写队列，而不是自动洗稿。

## 前置与输出

- 输入为 Originality、Substance、Template Language 和 Citation 审计报告。
- 输出 `manual_rewrite_queue`，按严重度、证据缺口、依赖和建议动作排序。
- 每项保留原段落定位与理由；不直接覆盖已有草稿。

## 参考

- [项目契约](../../shared/project-contract.md)
