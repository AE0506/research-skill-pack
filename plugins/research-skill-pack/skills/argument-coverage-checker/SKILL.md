---
name: argument-coverage-checker
description: Audit whether each manuscript argument has sufficient evidence, literature support, scope discipline, and no logical jump. Use explicitly before drafting.
---

# Argument Coverage Checker

逐节点检查论证树的证据、文献、范围、重复和逻辑跳跃。

## 前置与输出

- 输入为 Argument Tree、Claim Graph、Evidence Package 和 Protocol。
- 输出 `argument_coverage_report`，按完整、缺文献、缺证据、因果越界、冲突或重复分类。
- 无证据主张只能标为待补，不得被批准进入 Results。

## 参考

- [项目契约](../../shared/project-contract.md)
