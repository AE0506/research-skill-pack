---
name: central-thesis-builder
description: Build a bounded central thesis from confirmed research questions, protocol, and verified evidence. Use explicitly for an evidence-linked manuscript spine.
---

# Central Thesis Builder

从已确认的研究问题、Protocol 与可用证据提出可检验的中心论点；没有足够证据时只输出候选论点和缺口。

## 前置与输出

- 读取项目契约、Research Question、Protocol、Claim Library 与 Verified Evidence Package。
- 输出版本化 `central_thesis` artifact，列出主张范围、依赖、反例和未决证据；不写正文、不创造事实。
- 任何因果、普遍性或贡献表述必须受设计与证据范围约束。

## 参考

- [项目契约](../../shared/project-contract.md)
- [状态机](../../shared/state-machine.md)
