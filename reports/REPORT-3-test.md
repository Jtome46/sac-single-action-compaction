# 第二部分：优化实现、三轮迭代与测试报告

> **状态更新（2026-11-14，按要求回退）**：`plugins/dsh-sac-compact` 已回退到 v10 之前的版本（`lib/sac-ledger.js` 删除，预设配置恢复原样，22 个原有测试全绿）。本文 §1.1 的插件改动仅作历史记录；**v10–v13 的机制目前只存在于 `harness/` 测试台**，不在 DSH 插件里。

> 对应第一部分 [`REPORT-3-analysis.md`](REPORT-3-analysis.md) 的 5 条致错机理（M1–M6）与 7 个优化方向（D1–D7）。
> 本轮把方向落成可测试的机制，做 3 轮迭代。每轮以**确定性回放/脚本化端到端**为主证据，真实模型矩阵作为佐证（受端点稳定性限制，见 §3.3），并明确写出哪些假设被证伪。

---

## 0. 结论摘要（先看这里）

1. **确定性证据（不依赖模型、可复现）**：在真实失败会话的轨迹上，
   - v9：结论时上下文里 **0/10** 张图像观测，16 次重复动作不可见，finish 无门控 → 与真实错误完全一致；
   - v10：**6/10** 张图像被钉住，16 次重复被账本标出；
   - v11/v12：门控**放行**了"5 枚"这个结论（因为脚本给出的"证据"字段非空、且只有一条 claim）；
   - v13：门控**拦截**——"seal_count=5 只来自脚本阈值，需要独立观测"。
2. **这条链说明了三件事**：观测丢失（v10 修）、证据登记（v11 只解决了"有没有写"，没解决"写得对不对"）、代理指标（v13 才真正拦住）。
3. **真实模型矩阵**（`deepseek-v4.1-flash`，同一任务、同一真值）的结果见 §3.3；端点在高并发/长生成下会 `RemoteDisconnected`，矩阵规模因此受限，凡是没能跑完的格子都如实标注为"未完成"，不用它下结论。
4. **插件侧**已落地 v10：`ledger` / `pinImages` / `repeatGuard` / 懒安装（修 M6 的静默降级），27 个单元+集成测试全绿。

---

## 1. 实现清单

### 1.1 插件（真实产品代码，`plugins/dsh-sac-compact`）

| 文件 | 变更 |
|---|---|
| [`lib/sac-ledger.js`](../plugins/dsh-sac-compact/lib/sac-ledger.js) | 新增：确定性证据账本（`buildLedger` / `renderLedger` / `findRepeats` / `ledgerSurvived`） |
| [`lib/sac-policy.js`](../plugins/dsh-sac-compact/lib/sac-policy.js) | 新增 `pinImages` / `ledger` / `repeatGuard`；`planSacSpan` 支持图像钉住并在裁剪后重算 span 统计 |
| [`index.js`](../plugins/dsh-sac-compact/index.js) | 账本注入状态更新；懒安装状态模板（修 M6）；重复动作检测日志；`hasImage`/`collectCalls` |
| [`cordis.patch.yml`](../plugins/dsh-sac-preset/cordis.patch.yml) | 预设启用 `ledger: true`、`pinImages: 6`、`repeatGuard: true` |
| [`README.md`](../plugins/dsh-sac-compact/README.md) | 记录 v10 设计、配置与实测数字 |

### 1.2 测试台（`harness/`）

| 文件 | 变更 |
|---|---|
| `sac/tasks.py` | 新增 `seal_count` 任务（真实扫描件、真实真值 6 枚、评分含数量与名称） |
| `sac/agent.py` | v10–v13 特征；证据账本；重复守卫；`note` 工具；finish 门控；矛盾检测；交叉方法/证据新鲜度门控；图像从 tool 消息移到 user 消息（修端点兼容）；narration 不再被误判为终答 |
| `sac/prompts.py` | `STATE_V10/V11/V12/V13` 四套状态模板 |
| `sac/tools.py` | 沙箱暴露 `$SAC_PYTHON`（numpy/Pillow 只在捆绑运行时里） |
| `replay_probe.py` | 新增：确定性回放真实会话，统计"结论时还剩几张图/多少次重复" |
| `policy_sim.py` | 新增：把真实轨迹跑过 v9–v13 的策略，输出门控判定 |
| `seal_report.py` | 新增：印章任务专用结果表 |

### 1.3 任务与真值

- 文档：`平台二期上线试运行申请单.pdf` 的渲染图（`page.jpg`）+ 5 张审批行裁切（`row_01.jpg`…`row_05.jpg`）。
- 真值：**6 枚印章**（湖南经研电力设计有限公司、经研院×2、数字智能研究中心、发展策划部、科技数字化部），第一部分的复核图见 [`assets/gt_annotated.png`](assets/gt_annotated.png)。
- 评分：数量=6 且识别 ≥4 个名称 → 1.0；仅数量对 → 0.6；仅名称对 → 0.4；其余 0。
- 工具：`view_image` + `bash`（可用 `$SAC_PYTHON seals.py`，默认阈值 `0.72×max` → 恰好 5 个强响应，第 6 枚 score 59 被阈值排除——**故意保留原会话的陷阱**）。

---

## 2. 测试方法

三类证据，互相补位：

| 类型 | 是否调用模型 | 回答什么问题 | 复现命令 |
|---|---|---|---|
| 确定性回放 | 否 | 真实轨迹下，各策略保留/标出/拦截了什么 | `python3 harness/replay_probe.py work/sessions/single_action.jsonl`、`python3 harness/policy_sim.py …` |
| 单元/集成 | 否 | 机制本身是否正确（27 个用例） | `cd plugins/dsh-sac-compact && node --test test/*.test.js` |
| 模型矩阵 | 是 | 换了策略后模型是否真的答对 | `python3 harness/run.py --models deepseek-v4.1-flash --regimes fha,sac --state-versions v9,v10,v11,v12,v13 --tasks seal_count …` |

---

## 3. 迭代 1：v10 —— 证据账本 + 观测钉住 + 重复守卫

### 3.1 机制

| 机制 | 对应机理 | 实现 |
|---|---|---|
| 证据账本 | M1/M2 | 每次工具调用写 `(step, tool, args, 结果摘要)`；图像记路径+已看；账本每步注入状态更新且要求原样保留 |
| 观测钉住 | M2 | `planSacSpan` 把折叠区间的终点拉回到"最近 N 张图像之前"，N 默认 6 |
| 重复守卫 | M1/M3 | 同一 `(tool, args)` 再次出现时，账本标 `repeated_calls`，观测前缀 `[REPEAT] … earlier result: …` |
| 懒安装 | M6 | 状态模板在第一次 `agent/pre-step` 安装；`apply()` 时只做尽力而为，避免隔离组未挂载时静默退回 native |

### 3.2 确定性结果

`policy_sim.py` 在真实失败轨迹上的输出：

| 变体 | 结论时仍可见的原始图像 | 账本标出的重复动作 | finish 门控 | 触发原因 |
|---|---|---|---|---|
| v9 | 0 张 | 16 次 | 放行 | — |
| v10 | 6 张 | 16 次 | 放行 | — |
| v11 | 6 张 | 16 次 | 放行 | — |
| v12 | 6 张 | 16 次 | 放行 | — |
| v13 | 6 张 | 16 次 | 拦截 | seal_count=5 comes only from a script threshold; an independent observation is required |

- **0 → 6**：结论时仍可见的原始图像从 0 张变成 6 张（`row_03/04/05 + row_01/02 + hough_overlay` 的最后 6 次）。
- **16 次重复**全部被账本标出，而 v9 里它们对模型不可见。
- 但 v10 **不改变结论**：它只保证"证据还在、重复可见"，模型仍然可以用阈值关掉疑问。这正是第 2 轮要解决的问题。

### 3.3 模型矩阵

真实模型矩阵（`deepseek-v4.1-flash`，26 步预算，单并发）结果：

| 范式 / 版本 | 重复 | 分数 | 判定 | 声称数量 | 识别名称 | 步数 | 看图 | 重复动作 | 压缩 | 峰值上下文 | 墙钟 s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fha | 1 | 0.00 | ❌ | - | 0/5 | 24 | 11 | 0 | 0 | 12,938 | 244 |
| sac-v10 | 1 | 0.00 | ❌ | - | 0/5 | 0 | 0 | 0 | 0 | 0 | 10 |
| sac-v11 | 1 | 0.00 | ❌ | - | 0/5 | 0 | 0 | 0 | 0 | 0 | 10 |
| sac-v12 | 1 | 0.00 | ❌ | - | 0/5 | 26 | 15 | 2 | 20 | 4,873 | 321 |
| sac-v13 | 1 | 0.00 | ❌ | - | 0/5 | 26 | 14 | 3 | 19 | 6,040 | 350 |
| sac-v9 | 1 | 0.00 | ❌ | - | 0/5 | 0 | 0 | 0 | 0 | 0 | 110 |

必须如实说明：**6 个格子（另加一次 32 步的 v9 复跑）没有一个拿到最终答案**。原因分两类：
- 基础设施：`HTTP 502`、`SSL: UNEXPECTED_EOF_WHILE_READING`、`RemoteDisconnected` 各毁掉 1–2 个格子；
- 预算：v12/v13 在 26 步内用了 45–46 次请求、19–20 次压缩，模型一直在看图/写脚本，**没有收敛到 finish**（真实会话用了 83–104 步，26 步明显不够）。

补充：把 v9 的预算放到任务上限（**32 步**）再跑一次（`results/iter6b`），仍然没有收敛——57 次请求、25 次压缩、27 次看图、峰值 5,326 tokens，最终 `action budget exhausted`。这说明在**降采样后的图像 + 32 步预算**下，SAC 会话依然难以收敛；真实会话是在 200 DPI 原图、83 步下才收尾的。这既是任务难度问题，也是 SAC 的结构问题：每步重写状态让模型不断「重新开始」，收敛所需的步数被放大。

因此**正确性对比不建立在这张表上**，它只用来说明两件事：(a) 端点与预算限制，(b) 在 harness 里 v12/v13 用了 14–15 次看图（FHA 11 次），观测被保留后模型更愿意复核，但**没有自动带来收敛**——这本身是第 3 轮之后的新问题（见 §7 方向 6）。

> 迭代 1 的模型侧结论：证据保住了，但模型不一定用；收敛需要额外的「该收尾了」信号。

### 3.4 迭代 1 的结论

- 观测钉住是**必要**的：没有它，任何"再确认一下"都要以一次新的看图 + 一次新的折叠为代价；
- 但它**不充分**：证据在上下文里，不等于模型会用它。第 2 轮引入"证据必须登记"。

---

## 4. 迭代 2：v11 —— 结构化状态 + 证据登记 + finish 门控

### 4.1 机制

- 状态模板改为证据优先的固定 schema：`OBJECTIVE / VERIFIED_FACTS(←evidence) / CLAIMS / IMAGES_OBSERVED / OPEN_QUESTIONS / NEXT`；
- 新增 `note(subject, value, evidence, method)` 工具，`finish` 前必须至少登记一条**带证据**的 claim；
- 没有 claim、或 claim 的证据为空 → `finish` 被拒绝，并提示补证。

### 4.2 确定性结果

`policy_sim.py` 显示 v11 **放行**：

```
v11 | 6 张 | 16 次 | 放行 | —
```

原因很直接：脚本化 agent 登记的是 `seal_count=5, evidence="hough: 5 circles above 0.72*best, 18 weak responses dismissed as noise", method="script"`——**证据字段非空、格式合规**。门控只检查"有没有写证据"，不检查"证据是不是观测"。

### 4.3 模型矩阵

模型侧与迭代 1 同表（v11 因端点 502 在第 0 步失败，未取得可用数据）；机制侧的结论来自 `policy_sim`：门控放行。

### 4.4 迭代 2 的结论

- 证据登记把"我数完了"从自我声明变成了可检查的记录，**但没有解决"用代理指标冒充观测"**；
- 这是一次被证伪的假设：**"强制写证据"≠"证据正确"**。第 3 轮必须检查证据的**来源**。

---

## 5. 迭代 3：v12 → v13 —— 代理指标交叉验证 + 证据新鲜度

### 5.1 机制

| 机制 | 实现 | 针对 |
|---|---|---|
| 矛盾检测（v12） | 同一 `subject` 出现两个不同 `value` 且没有跨方法确认 → 拒绝 finish，要求用**不同方法**复核 | M4/M5 |
| 交叉方法门控（v13） | claim 的 `method` 是脚本/检测器时，必须有同主题、**不同方法**的第二条 claim | M5 |
| 证据新鲜度（v13） | 结论涉及图像时，最后一次**原始**图像观测必须在最近 3 步内（overlay/mask 等派生图不算） | M2 |

### 5.2 确定性结果

`policy_sim.py`：

```
v12 | 6 张 | 16 次 | 放行 | —                       （只有一条 claim，矛盾检测不触发）
v13 | 6 张 | 16 次 | 拦截 | seal_count=5 comes only from a script threshold; an independent observation is required
```

- v12 的失败是**可预期的**：矛盾检测依赖"模型自己登记了第二条 claim"，而真实会话里模型根本没有登记第二条。
- v13 把条件反过来：**只要结论来自脚本，就必须有独立观测**——不依赖模型自觉。

### 5.3 模型矩阵

模型侧与迭代 1 同表（v13 在 26 步内未收敛）；机制侧的结论来自 `policy_sim` 与下面的脚本化端到端测试。


### 5.4 脚本化端到端测试（不依赖外部模型）

`harness/scripted_seal_test.py` 用一个确定性的「脚本模型」重放真实轨迹（看整页 → 看 5 行 → 跑检测器 → 答 5），并在 `finish` 被拒时按门控提示补一次独立观测：

| 变体 | 分数 | 通过 | 门控拦截次数 | 最终答案（截断） |
|---|---|---|---|---|
| v9 | 0.00 | ❌ | 0 | 结论：共 5 枚印章……圆检测恰好有 5 个强响应圆，其余弱响应属于签名误检。 |
| v13 | 1.00 | ✅ | 1 | 结论：共 6 枚印章。逐枚为：湖南经研电力设计有限公司…科技数字化部。 |

这是本轮最直接的机制证据：**同样的错误轨迹，v9 被接受，v13 被拦下并迫使模型重新看图，最终答对。**

### 5.5 迭代 3 的结论

- 三轮下来，真正能拦住这次错误的最小机制组合是：**钉住观测（v10）+ 结论必须来自观测而非阈值（v13）**；
- v11/v12 的价值在于把"证据"和"矛盾"变成显式对象，但**不能替代 v13 的来源检查**。

---

## 6. 回归测试

| 测试 | 结果 |
|---|---|
| 插件单元+集成（27 例） | ✅ 27/27 |
| 既有 5 类任务回归 | 未完成：端点在本轮后段持续 502/SSL 断连，回归矩阵未能取得可信数据（不作为结论） |
| 新任务 seal_count（真值 6） | 见 §3–§5 矩阵 |

---

## 7. 测试后的优化方向（更新版）

1. **把"证据来源"变成一等公民**：`note()` 的 `method` 不应是自由文本，而应是枚举（`visual:<path>` / `script:<cmd>` / `read:<path>`），这样门控可以机械判定"是否独立"。
2. **派生图与原始图分离**：v13 已经用文件名规则区分，正确做法是工具层标注 `derived_from`，避免"看了 overlay 就算看过原图"。
3. **证据新鲜度应绑定到 claim，而不是全局**：现在只要求"最近看过图"，更强的是"这条 claim 引用的图必须在窗口内"。
4. **账本要能反向检索**：账本现在是"最近 N 条"，长任务里应支持 `recall(evidence_id)`，让模型按需取回被折叠的原始观测。
5. **状态更新应增量而非重写**：v10–v13 仍是"每步重写一段状态"，下一步应改成 append-only 的事实表 + 指针，彻底消除"摘要的摘要"。
6. **把门控做成可观测指标**：`gate_blocks`、`ledger_drops`、`repeat_rate` 应进入会话遥测，才能在生产里发现"压缩导致质量下降"。

---

## 8. 诚实声明与限制

1. 真实模型矩阵受端点稳定性限制（`RemoteDisconnected`、长生成被断开），部分格子未完成，已在表中标注；**结论主要建立在确定性回放 + 27 个机制测试上**，矩阵作为佐证。
2. `policy_sim.py` 模拟的是**策略**而不是模型：它证明"门控会拦/不会拦"，不能证明"模型被拦后一定改对"。
3. 单次会话有随机性；本次真实会话的 5 vs 6 是事实，但"v9 必然答错"不成立。
4. 插件侧只落地了 v10（账本/钉住/重复守卫/懒安装）；v11–v13 的门控目前在 harness 里验证，移植到 DSH 需要 `note`/`finish` 级别的工具拦截能力，属于下一步工作。

---

## 9. 追加：A1（懒安装）+ A3（遥测）落地与回归

按后续要求，插件在回退后又单独落地了两个**与任务无关**的修复：

| 项 | 内容 |
|---|---|
| A1 懒安装 | `apply()` 尽力安装状态模板，首次 `agent/pre-step` 兜底重试；`Symbol.for` 标记防重复包装；装不上时 `logger.error` 只报一次（不再静默退回 native） |
| A3 遥测 | 每 agent 计数器：`steps / compactions / foldedTokens / lastFoldActions / skipped / lastSkipReason / installAttempts / installFailures / installedOn / summarizeCalls / summarizeChars / summarizeErrors`；`telemetrySnapshot(agent)` 读取副本，`stateUpdateInstalled(engine)` 直接回答"装没装上"；每次折叠打一行带计数的日志 |

### 9.1 测试结果

| 测试 | 结果 |
|---|---|
| 插件单元+集成（原 22 + 新增 5） | ✅ **27/27** |
| 加载时序演示 `node test/late-mount.demo.mjs` | ✅ **PASS**（apply 时未装 → 首次 pre-step 装上 → 第二次不重复包装 → 折叠失败被计数） |
| 预设重导出检查 | ✅ `apply` / `stateUpdateInstalled` / `telemetrySnapshot` / `PAPER_STATE_PROMPT` 均可见 |
| 任务/会话特化扫描 | ✅ 插件包内零命中（`seal / 印章 / hough / row_N / 用户路径 / 会话 id`） |

演示脚本的关键输出：

```
1. apply() before the compaction group mounts
   installed? false (no engine yet)
3. first pre-step installs the template
   installed? true | summarize calls: 1
   telemetry: { steps: 1, compactions: 1, foldedTokens: 6, installedOn: 'pre-step', summarizeCalls: 1, ... }
4. second pre-step must not double-wrap
   summarize calls after 2 folds: 2 (must be 2)
5. a failing fold is counted, not thrown
   skipped: 1 | reason: compaction busy
RESULT: PASS
```

### 9.2 仍未验证的部分

- **真实 DSH 会话**没有重跑：从当前会话里无法新建一个 SAC 预设会话。要确认 A1 在生产路径生效，需在 GUI 新建会话后看日志里是否出现 `state update installed (pre-step)` 以及每步折叠行里的 `installed=pre-step`。
- A3 只落到日志与模块导出，**没有接入 GUI 的遥测面板**（需要 DSH 的 UI 侧接口，本次未做）。
