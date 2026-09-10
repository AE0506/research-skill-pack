---
name: research-evidence-lab
description: 为已确认研究设计登记真实数据、脱敏摘要、清洗版本、分析运行、结果与图表的完整谱系；用于可复现的数据与证据管理，不读取原始敏感数据、不补造数据或实验结果。
---

# Data & Evidence Lab｜数据、实验与证据工作台

将 Research Protocol 中的“应该收集什么证据”转化为真实、可追踪、可复核的数据与分析记录。它协助执行与登记，不替用户完成真实问卷招募、访谈、实验或数据采集。

## 使用前先读

- [项目契约](../../shared/project-contract.md)：数据资产、数据版本、分析运行、结果、图表和 Verified Evidence Package 的字段。
- [状态机](../../shared/state-machine.md)：仅在 `design_ready` 运行；满足真实性和谱系条件后才能进入 `evidence_ready`。
- [V1 指标规范](../../shared/metrics-v1.md)：证据资格、真实性声明和结果解释分级。

## 前置条件

需要已确认的 Research Protocol、变量字典与 Hypothesis–Field 对齐表。每个假设都必须连接到可观察证据和计划数据字段；发现无对应字段时，停止并要求返回 `$research-design` 修复。

## 数据谱系模型

严格维护不可倒置的链条：

```text
Raw Data
→ Processed Data
→ Analysis Dataset
→ Analysis Run / Code
→ Tables and Figures
→ Verified Evidence Package
```

- **Raw Data**：只登记路径、SHA-256、权限、来源、许可、采集日期、真实性声明和敏感性等级。默认不读取、更不上传给模型。
- **Processed Data**：每次清洗独立版本，记录父版本、转换规则、缺失/异常处理、去标识化状态和责任人；禁止覆盖 Raw Data。
- **Analysis Dataset**：记录字段、派生变量、样本筛选、行数/列数、与假设的对应关系。
- **Analysis Run**：记录 Python/R/SPSS/Stata 脚本路径或操作日志、运行环境、参数、随机种子、输入/输出版本、时间、执行者和运行状态。
- **Result / Figure**：记录生成分析运行、对应假设、统计值、图表位置、解释边界和人工核验状态。

## 工作流

1. 创建 `Data & Experiment Register`：问卷、公开数据、行为日志、访谈、实验或其他来源分别登记数据权利、真实性和伦理边界。问卷支持的是题项、量表、反向题、注意力检测与数据字典设计；不代表系统代填或补样本。
2. 对每次真实数据导入，仅登记最小必要元数据与 hash。若用户明确批准提供脱敏摘要，限于完成当前分析所需的最小字段与范围。
3. 建立清洗计划和版本记录：绝不静默覆盖，清洗步骤必须可复现并对每项规则写明理由。
4. 建立分析计划到运行的映射：一个结果必须能追溯到数据版本、代码/日志和对应假设；不带谱系的数字只能标为未验证，不能进入论文 Claim。
5. 执行/记录统计检验、可视化和诊断时，报告真实的显著/不显著、样本限制、效果量和模型假设。分析设计不支持因果时，禁止生成因果措辞。
6. 仅将来源真实、谱系完整、用户/研究者已核验、且符合 Protocol 的结果放入 `Verified Evidence Package`；其余作为草稿、待核验或被拒绝记录。
7. 生成 Data Lineage Report 与 Evidence Readiness Check。所有核心结果满足要求才建议推进 `evidence_ready`，否则保持阻塞并列出缺口。

## 绝对禁止

- 补造、插补为“真实”、修改原始数据以取得显著性，或虚构实验/访谈/问卷运行记录。
- 将模拟示例、合成 fixture 或 AI 生成数字写成项目真实发现。
- 未经明确许可读取、传输或展示含可识别个人信息、原始敏感问卷、音视频、医疗/教育等受限数据。
- 无数据谱系即把结果输出为论文证据；无设计支持即把相关写为因果。

## 输出

- Data & Experiment Register、Raw/Processed/Analysis Dataset 版本索引。
- 清洗日志、分析运行日志、结果/图表登记和 Data Lineage Report。
- Verified Evidence Package 或明确的 `blocked` 原因。
- 下一步仅在 `evidence_ready` 后建议 `$paper-architect`；不得直接生成论文 Results。
