---
name: chapter-mapper
description: Map an approved argument tree to the target manuscript profile's chapters without turning chapter headings into unsupported claims. Use explicitly.
---

# Chapter Mapper

把论证树映射为目标 profile 的章节容器，而非从目录倒推论证。

## 前置与输出

- 读取目标写作 profile、Argument Tree 和 Research Protocol。
- 输出 `chapter_map` artifact，注明每章目的、论证节点、证据来源和禁写内容。
- 无关内容应被移除或标记为未纳入，不以凑字数保留。

## 参考

- [项目契约](../../shared/project-contract.md)
