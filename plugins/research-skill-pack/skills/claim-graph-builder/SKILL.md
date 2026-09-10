---
name: claim-graph-builder
description: Map claim dependencies, support, contradiction, and manuscript use without inventing evidence. Use explicitly for logical traceability.
---

# Claim Graph Builder

建立 Claim 之间的支持、冲突、依赖和引用关系图，供写作与审计复用。

## 前置与输出

- 读取 Claim Library、Evidence Graph、Argument Tree 与 supersession 状态。
- 输出 `claim_graph` artifact；冲突、撤稿影响和无证据节点必须单列。
- 图谱不自行判断外部事实真实性，仍以核验状态为准。

## 参考

- [项目契约](../../shared/project-contract.md)
