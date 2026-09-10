---
name: research-design
description: 将已通过立项的中文本科信息管理或社科实证研究问题转化为可执行、可审计的研究方案；用于理论、变量、样本与分析计划设计，不虚构数据、不把相关设计包装成因果研究。
---

# Research Design｜研究设计

基于已确认的研究问题、Context Brief 和本地证据库，生成可审查的 Research Protocol。首版服务中文本科信息管理及相邻社科实证项目，不切换到计算机模型训练/消融实验模式。

## 使用前先读

- [项目契约](../../shared/project-contract.md)：Research Protocol、变量字典、分析计划及依赖字段。
- [状态机](../../shared/state-machine.md)：仅在已确认 GO/CONDITIONAL GO 后创建设计；必要前置缺失时保持 `blocked`。
- [V1 指标规范](../../shared/metrics-v1.md)：研究设计适配度、Fatal Flaw 和证据分级。

## 前置条件

需要：已确认的 Context Brief、已确认的 Review Board 决策、具体 Research Question、至少一个可定位的 Gap Card，以及支撑理论/构念选择的本地文献证据。若 Conditional GO 有未完成条件，应先显式显示条件，不能把草案伪装成可实施方案。

## 工作流

1. 建立可追溯链条：

   `Research Question → Theory → Hypothesis/Proposition → Construct → Variable → Operationalization → Observable Evidence → Data Field → Analysis → Interpretation Boundary`

2. 明确研究类型与识别边界：描述性、关联性、比较性、预测性或在有充分设计前提下的因果性。横截面问卷默认只能支撑关联解释。
3. 生成 Theory/Concept Model：每个假设写明理论机制、正反证据、方向、适用边界与当前是否可检验。中介、调节和异质性仅在理论与数据支持时使用，不能作为“高级感装饰”。
4. 生成变量与测量字典：概念定义、变量角色、操作化、题项/量表来源、量表版本、编码、范围、缺失规则、潜在混杂变量与测量风险。未核验量表只可列待核验。
5. 生成数据/样本计划：研究对象、纳入/排除标准、抽样、数据来源、权限、样本量理由、招募路径、伦理与脱敏需求、时间线。没有真实获取路径即提出 Fatal Flaw 或 Conditional GO 条件。
6. 生成预分析计划：描述统计、主分析、模型假设检查、稳健性/敏感性分析、缺失/异常处理、效果量和解释规则。明确何时只能报告相关、何时不得过度外推。
7. 进行 Hypothesis–Field 对齐检查：每个假设必须有可观察证据与未来数据字段；无对应字段的假设标为不可检验并阻止进入 `$research-evidence-lab`。
8. 将 Protocol 作为用户待确认草稿写入新 artifact；确认后状态进入 `design_ready`。

## 质量与安全规则

- 研究设计是建议和文档，不替代伦理审批、导师决定或真实统计咨询。
- 不提供伪造的功效计算、样本量结论、量表信效度或因果识别保证；缺乏输入时明确说明所需资料。
- 不读取、上传或生成原始敏感数据；只登记数据计划和最小脱敏信息。
- 所有理论、量表和方法依据须链接 Claim/Evidence；未核验依据不进入可投稿证据。

## 输出

- `research-protocol`：问题、理论、假设、模型、变量、样本、数据、分析、风险和解释边界。
- `variable-dictionary` 与 Hypothesis–Field 对齐表。
- 已确认时的 `design_ready`；否则列明可修复条件并路由回 Review Board 或 Literature OS。
