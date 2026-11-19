# SAC 单动作压缩：论文复现 + DSH 上下文压缩插件 + 双模型测试报告

> 论文：[*You don't need long context*](https://arxiv.org/abs/2611.05306)（arXiv:2611.05306，NVIDIA，2026-11）
> 实现：`plugins/dsh-sac-compact`（DeepSeek Harness 插件）+ `harness/`（可复现测试台）
> 约束：模型输入上限 **130,172** tokens，输出上限 **8,192** tokens
> 模型：**qwen3.7-flash**、**deepseek-v4.1-flash**（OpenAI 兼容端点）

## 目录

| 路径 | 内容 |
|---|---|
| [`paper.pdf`](paper.pdf) / [`paper.txt`](paper.txt) | 论文原件与提取文本 |
| [`docs/paper-notes.md`](docs/paper-notes.md) | 论文精读笔记（术语、三种范式、实验、失效模式） |
| [`docs/ecosystem-survey.md`](docs/ecosystem-survey.md) | 社区插件调研（dsh-live-compact 等 4 个）与本项目借鉴点 |
| [`plugins/dsh-sac-compact/`](plugins/dsh-sac-compact/README.md) | **上下文压缩插件**（v9 管线：inline 状态 + ledger + checklist + recall；策略层 + 41 个测试） |
| [`plugins/dsh-sac-preset/`](plugins/dsh-sac-preset/README.md) | **独立 Agent 预设**（`standard` + SAC，只在选定会话里生效，用于真实 GUI 测试） |
| [`harness/`](harness/) | 测试台：模型客户端、token 计量、工具沙箱、5 类任务、矩阵运行器 |
| [`benchmarks/`](benchmarks/README.md) | 论文同款测试集（SWE-bench Verified 500 / τ²-bench 184 golden set / LOONG 1,600，均已下载校验） |
| [`docs/VERSIONS.md`](docs/VERSIONS.md) | **版本表**：插件线（iter0–iter4 / v9）与测试台线（v1–v13）的对应、证据与状态 |
| [`docs/bench-methodology.md`](docs/bench-methodology.md) | **标准基准测试台**：真实 `dsh headless` 会话、两个 profile、隔离方式、三个基准的适配与判分 |
| [`harness/bench/`](harness/bench/) | 基准适配器 + 并行矩阵（`loong.py` / `swe.py` / `tau2.py` / `runner.py` / `matrix.py` / `report.py`） |
| [`reports/BENCH-REPORT.md`](reports/BENCH-REPORT.md) | **第四轮报告：三个标准基准 × GLM-5.3-Inner × SAC 插件，4 轮迭代**（含优化方向） |
| [`reports/BENCH-REPORT-128K.md`](reports/BENCH-REPORT-128K.md) | **128K 优化报告（2026-11-17）**：插件瘦身/限长/裁剪/硬预算 4 项改动，全量 12 任务 × n=3，token −56%、峰值 116K→50K |
| [`docs/SESSION-SURVEY.md`](docs/SESSION-SURVEY.md) | **工作区 12 个历史会话普查**：各会话主题/产出/状态，管线版本与 provider 怪癖 |
| [`work/goal_round1/ITERATIONS.md`](work/goal_round1/ITERATIONS.md) | 128K 优化线 iter5–iter10 的逐轮数据与结论 |
| [`reports/REPORT.md`](reports/REPORT.md) | 第一轮报告：论文复现 + v1–v4 迭代（7 任务 × 3 范式） |
| [`reports/REPORT-2.md`](reports/REPORT-2.md) | 第二轮报告：百万级仓库 + 真实会话 + v5–v8 迭代 |
| [`reports/REPORT-3-analysis.md`](reports/REPORT-3-analysis.md) | **第三轮（1/2）：两个工作区「二期申请单印章」会话的深度分析**——SAC 为什么把 6 枚数成 5 枚 |
| [`reports/REPORT-3-test.md`](reports/REPORT-3-test.md) | **第三轮（2/2）：优化实现 + 三轮迭代 + 测试报告**（v10–v13） |
| [`results/`](results/) | 每次矩阵运行的 JSONL 原始结果与日志 |

## 标准基准测试（GLM-5.3-Inner，4 轮迭代）

`reports/BENCH-REPORT.md` 记录了一次独立的基准测试：把插件放进真实的 `dsh headless` 会话，
在 **Loong、SWE-bench Verified、τ²-bench** 上跑，与不挂 SAC 的同模型基线（FHA）对比。

| 基准 | 配置 | 结果（SAC vs FHA） |
|---|---|---|
| Loong（长输入阅读） | 严格 SAC（每动作折叠） | 峰值 **6.7K vs 29.3K**，准确率 0.933 vs 0.80，总 token +44% |
| SWE-bench Verified（3 个 sympy 实例） | 严格 SAC | 3/3 vs 3/3，峰值 8.8K vs 14.1K，总 token +41%，墙钟 4.8× |
| SWE-bench Verified | **SAC-2 + 保留最近观测**（iter4） | 3/3 vs 3/3，总 token **0.79M vs 1.23M（−36%）**，峰值 −55%，墙钟 1.6× |
| τ²-bench（静态计划变体） | SAC-2 | 0.70 vs 0.57（噪声内），折叠 0 次 |

> **2026-11-15 更新**：插件已升级为 **v9 管线**（inline 状态 + ledger + checklist + recall + 自适应预算，
> 41 个测试全绿）。抽测：Loong 两题 1.0、总 token 106K vs FHA 180K（−41%）；SWE `sympy-24066` 1.0，
> 但 52 次折叠使墙钟 29 分钟（FHA 4.5 分钟）。详见 [reports/BENCH-REPORT.md](reports/BENCH-REPORT.md) 附录 B。

复现：`cd harness && python3 -m bench.matrix --bench loong,tau2,swe --arms sac,fha --iteration iterN --workers 4`。

## 128K 优化（2026-11-17，GLM-5.3-Inner）

在论文三测试集上把插件调到 **128K 上下文预算**下的最优：全量 12 任务（Loong 5 + SWE 3 + τ² 4），
每臂 n=5（120 格），同窗口 FHA 对照。

| 指标 | FHA（全历史） | 优化 SAC | 变化 |
|---|---|---|---|
| 任务加权均分 | 0.837 | **0.853** | +0.016 |
| 总 token（12 任务 × n=5） | 17,744,686 | **7,348,882** | **−58.6%** |
| 峰值上下文（最大） | **129,575**（3 次全量中 2 次 >128K：140,048 / 139,339） | **50,385** | **−61%** |
| SWE 3 题（n=5） | 3/3 | 3/3 | 持平；token 14.97M→4.82M（−68%），峰值 130K→37K |
| Loong 5 题均分（n=5） | 0.848 | **0.885** | +0.037 |
| τ² 4 题均分（n=5） | 0.702 | 0.702 | 持平（0 折叠） |

关键改动（`plugins/dsh-sac-compact` v1.1.0，48 个测试全绿）：

1. `stateInputLean`：状态更新请求不再重放会话 system prompt + 22 个工具 schema（实测 ≈4.8K tok/折叠，SWE 总 token −24.6%）；
2. `trimObservationOver=4000`：只裁超大观测，小测试输出逐字保留；
3. `stateMaxWords=400`：recap 限长（状态每请求重发，直接省 token）；
4. `contextBudgetTokens=96000`：逼近 128K 时强制折叠的硬保险；
5. `statePrompt: paper` + `actionsPerCompaction: 2` + `keepLastObservation`（v9 的 inline 对
   GLM-5.3-Inner 不可用：推理模型带 tool-call 的回复不输出文本块）；
6. paper 模板补 “输出契约 / 精确值” 两节；
7. 修复 `stateMaxTokens` 配置键未被 `resolvePolicy()` 识别的旧 bug。

另：**交付的 bundle 默认配置**（不经基准 profile 覆盖）在 SWE 上实测 token −84%、峰值 20.9K，
证明优化配置就是插件默认值本身。详见 [`reports/BENCH-REPORT-128K.md`](reports/BENCH-REPORT-128K.md)。

## 快速开始

```bash
# 插件单元 + 集成测试（22 个用例）
cd plugins/dsh-sac-compact && node --test test/sac-policy.test.js test/integration.test.js

# 单格测试
python3 harness/run.py --models qwen3.7-flash --regimes sac --tasks code_edit --verbose

# 完整矩阵（2 模型 × 3 范式 × 5 任务）
python3 harness/run.py --models qwen3.7-flash,deepseek-v4.1-flash \
    --regimes fha,eocc,sac --state-versions v1 --workers 4 --out results/iter1

# 汇总
python3 harness/report.py results/iter1/*.jsonl --out reports/iter1.md

# 印章任务（真实扫描件，真值 6 枚）与机制测试
python3 harness/run.py --models deepseek-v4.1-flash --regimes sac \
    --state-versions v9,v10,v11,v12,v13 --tasks seal_count --max-actions 40 --out results/seal
python3 harness/seal_report.py results/seal/*.jsonl --out reports/tables-seal.md
python3 harness/replay_probe.py work/sessions/single_action.jsonl   # 确定性：结论时还剩几张图
python3 harness/policy_sim.py work/sessions/single_action.jsonl      # 确定性：各变体的门控判定
python3 harness/scripted_seal_test.py                                # 端到端：v9 接受 5，v13 迫使复核后答 6
```

## 在 GUI 的独立工作区里测试 SAC

DSH 没有工作区级插件配置（工作区只是目录记录），插件作用域只有 profile 或 **agent 预设**。
所以「只在单动作测试工作区生效」的做法是装一个独立预设：

1. 安装 [`plugins/dsh-sac-preset`](plugins/dsh-sac-preset/README.md)（本机已装为 `@local/dsh-sac-preset`），
   Settings → Presets 里会出现 **SAC 单动作压缩**；
2. 工作区目录 `/Users/jtome/Downloads/单动作测试`（已建好），在 GUI 里 Add workspace 添加；
3. 只在该工作区新建会话时选 **SAC 单动作压缩** 预设——其它会话继续用 `standard`，完全不加载 SAC。

验证：会话里让它做几次工具调用，然后看该会话日志是否出现 `compaction/start` → `compaction/summary` → `compaction/end`，
以及 `dsh-sac-compact: folded N action(s)` 日志行。预设组合在会话创建时固化，改预设后需新建会话。

## 插件设计（三句话）

1. **它是策略层，不是第二个压缩后端**：挂在 `agent/pre-step` 上，调用已挂载的
   `ctx.compaction.compactRegion(start, end, agent, signal)`，复用后端的持久化事务、锁、checkpoint 标记与计量。
2. **压缩范围是纯函数**：`planSacSpan()` 从任务消息之后开始（吸收旧状态而不是叠加），到"工具配对平衡的切点"结束
   （绝不折叠未回答的工具调用），因此可以脱离运行时做单元测试。
3. **失败绝不影响对话**：没有后端、锁冲突、范围不平衡、摘要失败都会被捕获并只记录一次，下一步重试。

## 测试台设计

- **硬预算**：每次请求前用脚本感知的 token 估计器（CJK≈1 token/字，拉丁≈1/3.6 字）加上按
  `usage.prompt_tokens` 在线校准的系数来估算；超限则先裁剪最旧的大观测、再按"完整 assistant+tool 组"丢弃，
  并计入 `budget_violations` / `emergency_trims`。输出统一 `max_tokens=8192`。
- **三种范式**：FHA（全历史）、EoCC（阈值 96K 压缩）、SAC（每动作压缩，状态模板 v1–v4）。
- **五类任务**：多轮代码编辑、300KB 文档选择性阅读、三图多模态、长文档输出、状态保持（不可重读的抽签账本）。

## 结果速览

| 模型 | 范式 | 通过 | 平均分 | 峰值上下文 | 总输入 token | 请求数 |
|---|---|---|---|---|---|---|
| qwen3.7-flash | FHA（全历史） | 4/5 | 0.83 | 23,582 / **109,509** | 2,024,260 | 50 |
| qwen3.7-flash | EoCC（96K 阈值） | 5/5 | 1.00 | 4,622 / 14,445 | 140,618 | 34 |
| qwen3.7-flash | **SAC**（v1） | 4/5 | 0.94 | **1,867** / 2,686 | **271,847** | 133 |
| deepseek-v4.1-flash | FHA | 5/5 | 1.00 | 8,277 / 24,302 | 450,050 | 56 |
| deepseek-v4.1-flash | EoCC | 4/5 | 0.80 | 8,391 / 16,705 | 387,769 | 60 |
| deepseek-v4.1-flash | **SAC**（v1） | 4/5 | 0.94 | **2,282** / 3,314 | **224,779** | 96 |

（迭代 1 的 5 个短任务；SAC 在 deepseek 上经 4 轮迭代后达到 **7/7、平均分 1.00、零触顶、请求数 191**。）

第二轮（[`REPORT-2.md`](reports/REPORT-2.md)）在此基础上做了两件事：
- **百万级上下文编程任务**（992K tokens / 1,287 文件）：所有范式都用 **3–4K 上下文**解决——长输入不等于长上下文；
- **真实会话**（本机最耗上下文的 3 个 session，累计 195M / 30M / 51M 输入 token）：
  FHA 在 436/456 步上超出 130,172 预算，**只有 SAC 全程不超限**；
- **v5–v9 迭代**：把状态更新并进动作调用（v6）后，请求数 −68%、输入 token −62%，两个模型 8/8 全绿；
  再把"机器维护的全量命令账本"并进来（v9），真实会话的状态保真度从 0.19 升到 **0.90**，qwen 只要 105 次请求。

详细结果、失效案例与优化方向见 [`reports/REPORT.md`](reports/REPORT.md)；
每轮迭代的原始表格见 [`reports/tables-iter*.md`](reports/)；机器可读汇总见 [`results/summary.json`](results/summary.json)。