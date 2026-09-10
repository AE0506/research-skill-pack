---
name: citation-necessity-detector
description: Identify manuscript statements that require external citation versus project-specific reporting. Use explicitly before citation audit.
---

# Citation Necessity Detector

逐句判断外部事实、理论、定义、经验结论是否需要引用。

## 前置与输出

- 输入为带 Sentence Role 的草稿。
- 输出 `citation_necessity_report`；本研究方法和真实结果不要求外部引用但必须链接项目 artifact。
- 不依据模型记忆补充来源。

## 参考

- [项目契约](../../shared/project-contract.md)
