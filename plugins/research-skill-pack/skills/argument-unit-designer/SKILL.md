---
name: argument-unit-designer
description: Define one traceable argument unit linking a claim, evidence, literature support, interpretation, and implication. Use explicitly during manuscript architecture.
---

# Argument Unit Designer

为一个具体主张建立 `claim → evidence → literature support → interpretation → implication` 单元。

## 前置与输出

- 输入必须包含 Claim ID、证据定位、支持文献和范围限制。
- 输出 `argument_unit` artifact；证据或文献缺失时标为缺口，不能进入结果叙述。
- 不把相关性改写为因果，不把未核验来源升级为证据。

## 参考

- [项目契约](../../shared/project-contract.md)
