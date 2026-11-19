# SESSION-SURVEY：单动作压缩工作区会话普查

> 生成：2026-11-17 00:10 Asia/Shanghai ｜ 数据源：`~/.dsh/sessions/--Users-jtome-Downloads-~5355~52A8~4F5C~538B~7F29--/` 下 12 个 `session-*` 目录（zstd 压缩 JSONL，共约 1.33 万条事件）｜ 方法：`zstd -dc` + Python 解析，忽略 `request/header`、`assistant/attempt`、`job/*` 等大块流数据；时间统一为 Asia/Shanghai（UTC+8）。
> 说明：同目录另有 2 个 00:03 创建的非 `session-*` 目录（`7a863341`、`9d795f52`），是当前 goal 派生的子代理会话（本普查 + 另一份管线分析），不计入 12 个历史会话。

## 1. 12 个会话总表

| # | 会话 | 创建（+08） | preset / model | 主题（首条真实请求，截断） | 产出与状态 |
|---|---|---|---|---|---|
| 1 | `014de2b6` | 11-16 23:38 | standard / airongce `deepseek-v4.1-flash` | goal：找其他会话与管线版本、找 3 个测试集、优化 SAC、使 GLM-5.3-Inner 在 128K 上限下最优、迭代到明早 8:00（**与本次目标相同**） | 6 轮 goal 全部被 airongce **403 AUTH**（“无权访问 国网信息通信产业集团有限公司 分组”）打死；round 7 恢复，仅读了 README / VERSIONS / work 目录；23:59:39 用户**暂停 goal**。无任何产出。**interrupted/errored** |
| 2 | `17f3f2b9` | 11-14 10:19 | standard / airongce `deepseek-v4.1-flash` | “当前对话是否有 sac 单动作压缩的插件在运行”；“能不能新开一个工作区（名为单动作测试），只在那个区生效” | 确认插件未装入运行 profile；新建 `plugins/dsh-sac-preset`（cordis.patch.yml + sac/index.js + package.json）并用 plugin_manager 装入 desktop profile；更新 README。2 turn 完成。**finished** |
| 3 | `1df1b84f` | 11-15 23:25 | standard / **jms-proxy `GLM-5.3-Inner`** | “看看当前客户端里的单动作压缩插件和预设模式，是不是测试线里 V9 版本” | 确认客户端加载的正是 plugin-v9（bundle 为指向工作区源码的活链），插件测试 **41/41 全绿**，清理临时文件；1 次 500 重试。**finished** |
| 4 | `2959e7c1` | 11-14 00:02（header 10:21） | standard / airongce `deepseek-v4.1-flash` | goal①：读 arXiv 2611.05306 → 实现 SAC 压缩插件 → qwen3.7-flash / deepseek-v4.1 测试 → 报告；goal②：百万级上下文 + 3 个最耗上下文 session，做 4 轮迭代 | 实现 `plugins/dsh-sac-compact`、`harness/sac/*`，产出 REPORT.md、REPORT-2.md；两个 goal 分别 02:29 / 08:51 标记 complete；另答插件架构与“SAC 破坏前缀缓存”两问。**finished** |
| 5 | `4f0620b3` | 11-15 01:33 | standard / airongce `deepseek-v4.1-flash`（bench 子会话为 jms-proxy `GLM-5.3-Inner`） | goal：等 `e82fec10` 下完 3 个测试集，用最新 SAC 插件 + GLM-5.3-Inner 跑基准，尽量多 agent 并行 | 建 `harness/bench/*` 与 `sac-bench`/`fha-bench` profile，跑 iter0–iter4 + iter4rep，写 BENCH-REPORT.md 与 bench-iter*.md；后期把客户端插件升 v9、修 preset broken。16 turn。**finished** |
| 6 | `6046954a` | 11-13 23:53 | standard / airongce `deepseek-v4.1-flash` | 用户只输入“1” | 无工具调用，turn 被用户 abort。**interrupted（废会话）** |
| 7 | `947186b3` | 11-16 23:59 | standard / airongce `deepseek-v4.1-flash` | goal：与 014de2b6 相同的 128K 目标，Round 1/256 | **当前仍在跑**：拍 `plugin_versions/iter5` 快照、建 `work/dshhome` + 5 个变体 profile、跑 smoke；正查 inline `<state>` 不输出。**ongoing** |
| 8 | `ce82d60c` | 11-15 16:44 | standard / jms-proxy `GLM-5.3-Inner` | “请你介绍论文中，EOCC 和 SAC 的差别” | 读 paper.txt 给出 EoCC（会话末压缩、阈值触发、换会话）vs SAC（每动作后压缩、同会话状态）对比；1 次 500 重试。**finished** |
| 9 | `d978cfba` | 11-15 11:41 | standard / jms-proxy `GLM-5.3-Inner` | “你哈” | 打招呼并提示当前工作目录。**finished** |
| 10 | `e82fec10` | 11-15 00:47 | standard / jms-proxy `GLM-5.3-Inner` | “我想改进单动作压缩这个插件，请你找到原论文，告诉我他们用的什么测试集” | 定位论文 2.2 节；下载 Loong / SWE-bench Verified(500) / τ²-bench(184)，共 155MB 并校验；写 `benchmarks/README.md`。turn2 因 jms-proxy 502 报错，用户重发后 turn3 完成。**finished** |
| 11 | `f1af6184` | 11-13 23:56 | standard / airongce `deepseek-v4.1-flash` | goal：与 2959e7c1 完全相同（读论文 / 实现 / 测试 / 4 轮迭代） | 与 2959e7c1 **并行重复**的会话，产出同一套 plugin + harness + REPORT.md / REPORT-2.md；goal 02:29 / 08:51 complete。**finished（重复）** |
| 12 | `fdac86bd` | 11-14 14:55 | standard / airongce `deepseek-v4.1-flash` | goal：对比「单动作测试」与「DeepSeek_Harness_Draft」两个工作区的印章计数会话，分析 SAC 为何使答案错误、给优化方向、实践并做 3 轮迭代 | 写 REPORT-3-analysis.md / REPORT-3-test.md；插件加 A1 懒安装 + A3 遥测；harness v10–v13（仅 seal_count）；goal 22:15 complete；后答热更新机制。**finished** |

补充观察：
- 12 个会话 header 的 `agentPreset` 全是 `standard`；`2959e7c1`、`6046954a`、`f1af6184` 曾短暂选过 `cordis` 再切回。
- `2959e7c1` 的 header `createdAt`(10:21) 晚于首事件(00:02)，说明会话文件被复用/重建过；其与 `f1af6184` 是同目标的两条并行会话（时间线、写入文件、报告几乎一致）。
- `014de2b6 → 947186b3` 是同一目标的前后两次尝试：前者 pause，后者 23:59:45 新建会话并重新 create goal。

## 2. 从会话反推当前测试管线

### 2.1 两条版本线（详见 [VERSIONS.md](VERSIONS.md)）

**插件线（真实产品代码 `plugins/dsh-sac-compact`，快照在 `work/bench/plugin_versions/`）**

| 版本 | 核心改动 | 测试 | 状态 |
|---|---|---|---|
| `plugin-iter0` | A1 懒安装 + A3 遥测 + paper 模板（fdac86bd 修好的基线） | 27 | 历史基线 |
| `plugin-iter1` | 空状态重试 + `minSpanTokens` | 29 | 已并入 |
| `plugin-iter2` | `stateInputMaxChars` 裁剪 | 30 | **被证伪**，默认 0 |
| `plugin-iter3` | `keepLastObservation` | 31 | 已并入 |
| `plugin-iter4` | 仅配置：`actionsPerCompaction: 2`（SAC-2） | 31 | 基准最优配置 |
| **`plugin-v9`** | inline 状态 + ledger + checklist + recall + 自适应预算 + 版本化安装标记 | **41** | **当前客户端**（`statePrompt: inline`、APC 1、minSpanTokens 1200、budget 2048、adaptive/ledger/recall/checklist 全开） |
| `plugin-iter5` | 11-17 00:03 由当前 goal 拍的新快照，`index.js` 与 v9 逐字节相同 | — | 本轮迭代起点 |

另存在 `iter1-candidate`、`iter2-candidate`、`iter3-candidate` 候选快照目录。

**测试台线（Python `harness/sac/`，不是产品代码）**：`harness-v1`（论文附录 G.1 模板，最接近论文）→ v2 六段+预算 → v3 ACTION DIGEST → v4 ledger/recall/adaptive/ANCHORS → v5 checklist → v6 inline（**架构偏离**：论文是单独摘要回合）→ v7 read cache → v8 finish_guard（实为空操作）→ v9（v6 管线 + full ledger）→ **v10–v13 只在 seal_count 上验证**（v13 的 `cross_method` 有逻辑缺陷）。

### 2.2 基准迭代：profile 与配置

统一测试台：`sac-bench`（`dsh-base` + `dsh-headless` + `@local/dsh-sac-compact`）vs `fha-bench`（同版本 headless，不挂 SAC）；模型 `jms-proxy / GLM-5.3-Inner`，`maxTokens: 16384`；每格一次真实 `dsh headless`，隔离目录 `~/dsh-bench-runs/<iter>/<bench>/<task>__<arm>__r<n>`，web 关闭、`--approval-policy never`、单格超时 1800s。iter1–4 各 24 格（12 任务 × 2 臂），iter0 34 格（含后来被淘汰的任务），iter4rep 36 格（n=2）。

| 迭代 | 插件配置增量（相对上一轮） | 主结果 |
|---|---|---|
| iter0 | `statePrompt: paper`、APC 1、`minSpanChars 1200`、`stateMaxTokens 2048`（严格 SAC） | Loong 峰值 6.7K vs 29.3K（−77%）；SWE 总 token 2.39M vs 1.69M（**+41%**）、148 次折叠/10 次失败、墙钟 4.8× |
| iter1 | + `minSpanTokens: 400`、空状态重试（更高输出上限 + “直接输出”） | SWE 折叠错误 10→4（−60%）、总 token −21%、墙钟 −19%；Loong 单格 0.933→0.5（n=1 波动） |
| iter2 | + `stateInputMaxChars: 8000` | Loong token −46%（有效）但 SWE token **+20%**、墙钟 2.1× → **证伪**，默认回 0 |
| iter3 | `stateInputMaxChars: 0`、`keepLastObservation: true` | SWE 折叠 120→61、请求 −42%、墙钟 −28%、总 token −37%；代价：Loong 峰值 6.5K→24.5K |
| iter4 | + `actionsPerCompaction: 2`（SAC-2）+ 保留最近观测 | SWE 总 token 0.79M vs FHA 1.23M（**−36%**）、峰值 −55%、3/3 resolved、墙钟 1.6×；Loong 几乎不折叠（4 次）→ **SAC-2 只适合长 agent 任务** |
| iter4rep | iter4 配置，Loong/τ² 各 2 次重复 | Loong 峰值 15.9K vs 36.6K（−56%）、总 token 683K vs 945K（−28%）、准确率 0.79 vs 0.84（噪声内）；τ² 的 SAC 不触发折叠 |

### 2.3 证据地图

- 方法与版本：[bench-methodology.md](bench-methodology.md)（真实 headless 会话测插件，非 Python 复现）、[VERSIONS.md](VERSIONS.md)、[paper-notes.md](paper-notes.md)（harness 硬约束 130,172 in / 8,192 out）。
- 主报告：[BENCH-REPORT.md](../reports/BENCH-REPORT.md)（601 行：§0 结论摘要、§1 方法、§2 三个基准适配、§3–§7 五轮、§8 D1–D7 优化方向、附录 A 全量对比、附录 B v9 验证）；分轮表 [bench-iter0.md](../reports/bench-iter0.md)…[bench-iter4.md](../reports/bench-iter4.md)、[bench-iter4rep.md](../reports/bench-iter4rep.md)、汇总 [bench-all-iterations.md](../reports/bench-all-iterations.md)。
- 早期报告：[REPORT.md](../reports/REPORT.md)、[REPORT-2.md](../reports/REPORT-2.md)、[REPORT-3-analysis.md](../reports/REPORT-3-analysis.md)、[REPORT-3-test.md](../reports/REPORT-3-test.md)。
- 原始数据：`work/bench/results/*.jsonl` 共 20 个文件、**274 条记录**（iter0 拆成多批、iter1–4、iter4rep、v9port/v9port2、smoke_iter5；另有 `results_failed/iter2_*.jsonl` 一次失败运行）。每条记录含 `profile/score/metrics{requests,peak_context,compactions,wall_s,timed_out,session_id,model,diff}`。
- 日志：`work/bench/iter0*.log`、`iter1.log`…`iter4rep.log`、`v9port.log`；插件快照 `work/bench/plugin_versions/`；inline 冒烟 `work/bench/smoke_v9`…`smoke_v9i`（9 个目录）。
- 当前 goal 新增：`work/goal_round1/run_matrix.sh`（把 `DSH_HOME` 指到工作区内 `work/dshhome`、`BENCH_RUN_ROOT` 指到 `/tmp/dsh-bench-runs`）、`work/dshhome/profiles/sac-bench{,-b16,-b28,-i2,-p2,-p4}`。

## 3. 当前状态 / 未完成事项

### 3.1 四轮 BENCH-REPORT 的核心结论

1. 插件确实在真实会话里生效（每次 SAC 会话都有 `agent/pre-step → compactRegion`，压缩事件可从会话日志复核）。
2. SAC 收益**取决于任务形状**：长输入阅读（Loong）峰值 −77%；长 agent 任务（SWE）严格 SAC 总 token +41%、墙钟 4.8×。
3. 状态更新是主要成本：严格 SAC 占 SWE 总 token 52%，iter4 仍占 33% → D1（换小模型）是最大杠杆。
4. 工程化修复有效：空状态重试 + 最小折叠跨度把折叠失败从 10 次降到 0–4 次。
5. 一个被证伪的假设：裁剪状态更新输入对阅读任务有效、对 SWE 反效果（默认关闭）。
6. 准确率单格 n=1 波动大（Loong 0.933→0.5→0.933），确定性指标（token/折叠/错误/墙钟）才是主证据；仅 iter4 加了 n=2。
7. 最终建议：长 agent 任务用 `APC 2 + keepLastObservation`；长输入阅读用严格 SAC（可加 `stateInputMaxChars 8000`）；短任务不挂 SAC。
8. 唯一“准确率不降、总 token 低于 FHA”的配置是 iter4（SWE −36%），但它不适合阅读任务。

### 3.2 v9 inline 移植（v9port）

- 11-15 17:14 用户要求把客户端 SAC 插件升到 V9；17:24–20:09 先做 9 次 inline 冒烟（`smoke_v9`…`smoke_v9i`，alpha/bravo 数字问答；v9h/v9i 无 result，属失败尝试）。
- 18:13–18:21 `v9port.log` 只抽了 **3 个任务格**（Loong paper-L3-0、Loong financial-L2-5、SWE sympy-24066）× sac/fha 两臂 = 6 次运行：Loong 两格 SAC 均 1.0；SWE-SAC 空 diff 得 0.0。随后 `v9port2` 单独重跑该格才拿到 1.0（55 请求、52 次折叠、1764s；FHA 仅 269s）。因此 v9 **只有 3 个任务格的证据**，没有全矩阵。
- 附录 B 结论：v9 在 Loong 上总 token −41%、墙钟 −25%、准确率持平；SWE 能解对但慢 6.5×。**inline 模式对模型是否遵守格式极敏感**，首跑因不写 `<state>` 产生空 diff，插件后来加了 nudge 与 paper 回退。
- 20:01 用户重启后 GUI 看不到「SAC 单动作压缩」：根因是预设的 `sac-compact` 在 EntryGroup 上下文里报 `cannot get property "systemPrompt" without inject` 被标 broken → 补 `inject` 后修复；23:25 `1df1b84f` 验证 v9 已生效。

### 3.3 从未完成 / 仍在推进

- **v9 全矩阵缺失**：只有 3 个任务格，无法与 iter0–4 的 12 任务 × 2 臂直接横比；v9 的 inline 管线也没在 τ²/SWE 全量上验证。
- **D6 τ² 官方多轮桥接未做**：当前 τ² 是静态单轮计划变体（工具名 LCS 0.7 + communicate_info 0.3），不是官方多轮分。
- **D1/D3/D5/D7 均未落地**：状态更新换小模型（无 `stateModel`）、模板加“输出契约/精确值”两节、折叠熔断/预算策略、telemetry 出口（`/sac-status`）。
- **harness-v10–v13 只在 seal_count 上验证**，`cross_method` 有逻辑缺陷；没有回到三基准。
- **128K 目标从未真实压测**：bench 用 1M window + maxTokens 16384，12 个会话里没有任何一次上下文超限被 API 拒绝的记录。
- 当前 goal（`947186b3`，11-17 00:00 起）刚拍 `iter5`、建 b16/b28/i2/p2/p4 变体 profile（`minSpanTokens` 16K/28K、inline+APC2、paper+APC2/APC4），smoke 只跑了 2 格；已复现 inline `<state>` 不被模型输出（与附录 B 的格式敏感问题同源）。

## 4. GLM-5.3-Inner / provider 怪癖（会话日志实证）

### 4.1 端点与上下文口径

- jms-proxy：`openai-completions`，`baseURL: https://jtome46.top:11159/v1`，模型 `GLM-5.3-Inner`；凭证在 `~/.dsh/.credentials.yaml`（`JMS_PROXY_API_KEY` / `AIRONGCE_*`，本文不复述明文）。
- `request/context` 事件里 jms-proxy/GLM-5.3-Inner 与 airongce/deepseek-v4.1-flash 均报 `contextWindow: 1,000,000`；bench profile 另设 `maxTokens: 16384`。
- 但 goal 口径是 **128K 上下文上限**；harness 硬约束是 **130,172 输入 / 8,192 输出**（`harness/sac/agent.py` 的 `INPUT_BUDGET=130_172`、`OUTPUT_BUDGET=8_192`；docs/paper-notes.md §7）。三者不一致：128K 目前只是**目标约束**，从未在日志中被 API 拒绝验证。

### 4.2 实际观测到的 provider 错误（12 会话内 `llm/retry` 聚合）

| code | 典型消息 | 次数 | 场景 |
|---|---|---|---|
| AUTH 403 | `403: {"message":"无权访问 国网信息通信产业集团有限公司 分组 (request id: ...)"}` | 6 | `014de2b6` 的 6 轮 goal（airongce/deepseek-v4.1-flash）全灭；round 7 同 provider/model 恢复，说明是**分组权限瞬时问题**，不是模型能力问题 |
| SERVER 503 | `No available channel for model deepseek-v4.1-flash under group 国网信息通信产业集团有限公司 (distributor)` | 4 | `fdac86bd` 11-14 23:20（airongce 渠道消失） |
| SERVER 500 | `InternalServerError: ... Decode transfer failed for request rank=6/14 ... Failed to get kvcache from prefill instance, it might be dead; Model Group=GLM-5.3-Inner` | 2 | `1df1b84f`、`ce82d60c` 首步（jms-proxy PD/KV 传输故障） |
| SERVER 502 | `502 Bad Gateway`（nginx/1.22.1） | 5 | `e82fec10` turn2 连续 5 次重试耗尽 → turn 报错 |
| TIMEOUT | `pi-ai stream idle timeout after 300000ms` / `Request timed out.` | 21 + 3 | 最集中的会话是 `fdac86bd`、`4f0620b3`、`e82fec10`（三者重试总数 34/13/7，含其他 code）；长 benchmark/长会话最易触发 |
| TRANSPORT | `Connection error.` / `terminated` | 20 + 4 | 各会话均有，通常是重试后自愈 |

重试策略（事件里的 `policyKey`）：maxRetries 5，覆盖 `EMPTY_RESPONSE / RATE_LIMIT / SERVER / TIMEOUT / TRANSPORT`，退避 500ms→10000ms、抖动 0.1。**注意：12 个会话里没有一次真正触发 RATE_LIMIT（无 429/限流失败记录）**，主要故障是 300s 流空闲超时、连接错误、500/502/503 与 403 分组权限。

### 4.3 与模型行为有关的 quirk

- GLM-5.3-Inner 是推理模型：`stateMaxTokens: 2048` 可能被隐藏推理吃光导致状态更新返回空文本 → iter1 专门加了“空状态重试（更高输出上限 + 直接输出、不要推理）”。
- inline 模式（`statePrompt: inline`）要求模型自己写 `<state>` 块，GLM 经常不写或写超长：v9port 首跑因此空 diff，当前 goal 又在复现同一问题；插件靠 nudge + paper 回退兜底。
- 2026-11-14 23:20 之后 airongce 侧 `deepseek-v4.1-flash` 曾整体不可用（503 `model_not_found`），与 403 同属“国网信息通信产业集团有限公司”分组的权限/渠道问题，和 GLM-5.3-Inner 无关。