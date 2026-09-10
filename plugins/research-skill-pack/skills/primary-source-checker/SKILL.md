---
name: primary-source-checker
description: Identify when a manuscript should cite an original theory, measure, method, or empirical study rather than a secondary account. Use explicitly.
---

# Primary Source Checker

识别经典理论、量表、方法和关键经验结论的二手转引，并提示原始来源缺口。

## 前置与输出

- 输入为引用用途、Source Record 和可用原始来源记录。
- 输出 `primary_source_report`；原始来源不存在本地库时仅标待补，不能虚构 DOI。
- 合理综述引用可保留，但不能替代必要原始引用。

## 参考

- [项目契约](../../shared/project-contract.md)
