# v0.2 Beta 受控写入关卡

`research-state` 是 Research Skill Pack 的本地 MCP 服务。它把正常插件路径中的 canonical `.research/` 写入收敛为：读取状态 → 预检 → 提交 → 返回收据。它不联网、不读取登记的原始数据路径，也不向外部系统提交任何材料。

## 初始化与使用

在插件根目录初始化隔离运行环境：

```bash
cd plugins/research-skill-pack
python3 scripts/bootstrap_runtime.py
```

初始化会创建 Git 忽略的 `.runtime/`，其中固定安装 MCP、PyYAML 与 jsonschema。插件更新或重新安装后，应在 Codex 实际加载的插件目录再次运行该命令；运行环境不存在时，服务会以 `runtime_not_configured` 退出，不会降级为直接写文件。

服务公开三个工具：

- `inspect_research_project`：返回脱敏项目状态、artifact 索引、闸门、收据完整性和下一条规范化路由。
- `validate_canonical_change`：对一次候选 artifact/状态变更做只读预检，返回 `ready` 或 `blocked` 与 findings。
- `commit_canonical_change`：重新执行同一预检，成功后写入新 artifact、项目状态和脱敏收据；重复相同请求返回原收据。

每次变更必须携带 `request_id`、当前 `expected_mutation_revision`、`origin_skill_id`，以及 artifact 和/或状态迁移原因。已有 artifact 不能覆写；替代内容必须使用新 ID 和 `supersedes`。

## 受控范围与可审计性

[规范化写入策略表](../plugins/research-skill-pack/shared/canonical-mutation-policy-v0.2.yaml) 为全部 175 个已安装 Skill 逐项声明 `advisory`、`orchestrator` 或 `canonical_writer` 权限。29 种 canonical artifact 均有明确写入者；[规范化路由表](../plugins/research-skill-pack/shared/canonical-route-map-v0.2.yaml) 覆盖全部 12 个正常状态迁移。

成功提交会在 `<project>/.research/receipts/` 留下仅含 ID、状态、哈希、revision、来源 Skill、校验结果和时间的收据。写前日志位于 `<project>/.research/transactions/`：崩溃后服务会安全回滚未索引的新 artifact，或补写已完成变更的收据；无法安全判断时返回 `blocked`。

这不是操作系统级沙箱。用户、终端命令或其他程序仍可绕过 MCP 改文件；下一次读取和试跑审计会发现 manifest 或 artifact 哈希不匹配，并把该项目标为不可复核。它证明的是正常插件工作流的确定性约束与可追溯性，不证明模型一定遵守说明，也不证明研究结论或外部来源真实性。
