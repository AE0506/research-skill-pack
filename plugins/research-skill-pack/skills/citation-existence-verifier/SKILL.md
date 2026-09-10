---
name: citation-existence-verifier
description: Verify locally supplied citation metadata, DOI, author, title, and year consistency. Use explicitly; it does not query unconfigured online providers.
---

# Citation Existence Verifier

核对用户导入的引用实体是否在本地元数据、PDF 或 DOI 记录中一致。

## 前置与输出

- 输入为引用条目及本地 Source Record。
- 输出 `citation_existence_report`，区分一致、元数据冲突、缺资料和待人工核验。
- 未配置 provider 时返回 `not_configured`，不假装联网验证。

## 参考

- [Provider Interface](../../shared/provider-interface.md)
