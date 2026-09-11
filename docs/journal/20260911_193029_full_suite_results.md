# 2026-09-11 19:30:29 + full_suite_results

- 时区：Asia/Shanghai；本次恢复查看、结果核对和发布记录。
- 实测代码版本：0870769de27fe5cee0f2f550d9a8220748f284e8。
- 关联：[用户授权全量测评与实际启动](20260911_140717_full_suite.md)。
- 实际运行：runs/20260911_140804_nvidia_full_suite/。
- 控制台、退出码与显存记录：runs/20260911_140804_nvidia_full_suite_control/。
- 进度快照、汇总脚本及结果表：runs/20260911_140717_full_suite_session/。

## 用户原始输入

> 跑的怎么样了

## 助手用户可见回复原文

> 上一轮检查已完成 68/156 题：59 题通过、9 题功能失败，执行错误为 0。我现在查看最新进度，后台测评会继续运行。

> 已经全部跑完，服务器记录的结束时间是 **17:08**：
>
> - **156 题全部完成：109 题通过，47 题失败，通过率 69.87%。**
> - 执行错误 0，漏跑 0；总耗时约 **3 小时**。
> - 显存采样最大值约 **29.49 GiB**，结束后两个模型服务已回收。
>
> 后台任务在会话中断后继续完成了。我正在核对失败分类、同步完整结果，并把这次初版测评记录推送到仓库。

## 恢复连接与完成事实

- 旧 SSH 复用连接失效，BatchMode 返回 Permission denied (publickey,password)。
  用已有授权重建连接，未写入或显示凭据。
- 19:30:57 +08:00，实际读取服务器进度、metrics.json、gpu_summary.json 和 run.exit。
  完成时间来自原始 metrics，为 2026-09-11T17:08:30.076576+08:00；
  中断期间后台任务自行完成，不声称期间进行了人工监控。
- 156 题均已完成，PASS 109、FAIL 47、ERROR 0、NOT_RUN 0；独立通过率为 109/156，即 69.87%。
  总状态 FAIL，退出码 1，表示存在模型生成代码的编译或功能失败；整套工作流完整执行结束。
- 总耗时 10825.272651339881 秒，约 3 小时 25 秒。
- 每秒采样记录 10821 条，设备显存最大采样值 30201 MiB（29.4932 GiB），总显存 32760 MiB。
  最后显存 1 MiB，19:30 再检查仍为 1 MiB / 利用率 0%。采样值不称作连续测量的瞬时峰值。
- 服务器代码版本仍为 0870769，git status --short 为空；数据盘仍约剩 12 GiB。
- 原始结果目录约 37 MiB，控制记录约 940 KiB，会话记录约 232 KiB。
  使用 rsync -a 同步上述三个目录到本地 runs/，保留服务器原件和既有历史。

## 核对与结果归档

后续操作和实测核对结果在取得后追加。原始产物不进入普通 Git，轻量结果和完整逐题表进入本日志。
本次是固定配置下每题一次上游完整工作流；自验证一致率与官方独立结果分别统计。
自有 Docker 镜像、AMD、Vivado、论文 pass@k 和同权重裸跑对照仍是后续阶段。

## 完整结果核对

- 本地执行会话产物 summarize.py，退出码 0。核对 156 个题号、顺序、完整输出、原始 counts，
  所有实测 src/qiansai/*.py 哈希，逐题候选/参考/测试台哈希与固定数据来源，
  以及生成批次的 n=3、temperature=1.0、max_tokens=4096。未重跑模型。
- 本地与服务器 metrics、manifest、gpu_summary 三份文件 SHA256 完全一致。
  后台控制任务 15554 与工作流 15559 均已退出，两个子模块固定版本未改动。
- 原始 47 个 FAIL：output_mismatch 35、compile_failed 10、testbench_timeout 2。
  这只是原始评测阶段分类，不能直接解释为 47 个纯模型错误，原因见下方参考对照。
- 上游生成批次 V/P 各 283 批，返回候选各 849 份，共 1698 份。
  实际生成轮数：1 轮 87 题、2 轮 11 题、3 轮 58 题。
- 自验证一致率为 1.0 的 106 题中，官方原始判定 94 PASS、12 FAIL。
- 本轮 V/P 启动分别 59.0999 / 57.1290 秒，合计 116.2289 秒；全部单题耗时合计 10703.60 秒。
  单题均值 68.61 秒，中位数 38.85 秒，P95（nearest-rank）215.70 秒，最大 351.74 秒。
  最长题为 Prob146_fsm_serialdata，原始独立结果 FAIL。初始化缓存使本轮启动比首次部署更快。

助手用户可见回复原文：

> 失败分类已核对：**35 题输出不匹配、10 题生成代码编译失败、2 题触发官方测试台超时**。
>
> 另有 12 题虽然双模型自验证一致，仍未通过官方评测。完整日志已同步本地；我会将这些结果作为初版基线保留。

## 参考实现对照与明确更正

上面“10 题生成代码编译失败”的归因过早。继续逐份读编译日志后，发现参考输入本身也有
编译条件问题；下面保留原话并更正，不改写原始运行统计。

助手用户可见回复原文：

> 进一步检查发现，编译失败里有官方文件接口不一致，以及当前 Icarus 不支持的参考实现语法。因此，刚才把 10 题都称为“生成代码编译失败”不够准确。
>
> 我会补做一轮 CPU 对照：让官方参考实现接受同一套测试台，确认评测本身的问题范围，再发布最终说明。

- 读取 Prob099 的固定参考文件和测试台，证实前者端口是 y[5:0]、Y1/Y3，后者使用 y[6:1]、Y2/Y4。
  Prob151 的参考文件含枚举类型转换，实际 Icarus 11.0 编译日志报告该转换不受支持。
- 读取两个测试台的刺激次数及其 #1000000 超时分支，决定用参考实现作候选对照，
  以区别原始模型失败与参考实现也无法通过的评测条件。先确认所有 156 份参考文件各只有一个 module。
- 在服务器同一代码版本、同一 Icarus 11.0、同一 evaluate 函数执行 reference_control.py。
  只将原始参考实现的 RefModule 名称改为 TopModule，其他正文保持一致；原始参考和测试台仍作为评测输入。
  CPU 对照使用 4 个工作线程和原来 30 秒工具超时，不调用 GPU 或模型，不变更子模块。
- 对照目录 runs/20260911_193510_evaluator_reference_control/，19:35:19.730207 +08:00 完成，
  用时 8.88 秒，151 PASS / 5 FAIL。原始对照代码、工具版本、输入、日志、manifest 和 metrics 已同步本地。

| 题号 | 参考实现对照问题 | 实际证据 |
| --- | --- | --- |
| Prob082_lfsr32 | 官方测试台提前触发时限 | 参考对照 0/200000 不匹配，仍出现 TIMEOUT |
| Prob099_m2014_q6c | 参考实现与测试台的接口不一致 | Y1/Y3 与 Y2/Y4 不一致，原始 good1 也无法连接 |
| Prob141_count_clock | 官方测试台提前触发时限 | 参考对照 0/200000 不匹配，仍出现 TIMEOUT |
| Prob151_review2015_fsm | 当前 Icarus 不支持参考语法 | 枚举 cast 编译报错 |
| Prob156_review2015_fancytimer | 当前 Icarus 不支持参考语法 | 参考枚举 cast 编译报错；模型候选本身另有语法错误 |

- 五题均包含在原始 47 个 FAIL 中；另有 42 个 FAIL 发生在参考对照能通过的题目上。
  原始 109/156 和全部 156 个判定完整保留，没有事后删题、改分或改写固定数据。
  对照异常不代表相应模型生成正确；例如 082/141 的原始模型输出也存在大量不匹配。
- 生成 assessment.json、testcase_assessment.csv 和带参考对照列的逐题表，
  原来的 summary.json、testcase_results.csv 和原始 metrics 均保留。
- 未进行修改后的评测器复测或新模型采样，后续修复需另立版本与运行。

助手用户可见回复原文：

> 参考实现对照已完成：**151 题通过，5 题的评测条件存在问题**——1 题接口不一致、2 题参考代码语法不受当前 Icarus 支持、2 题测试台提前超时。
>
> 因此，初版原始结果仍保留为 **109/156 通过**，并单独标记这 5 题，避免把评测问题全部算成模型错误。

> 逐题结果表和参考对照已整理完成，服务器与本地结果的哈希一致。初版已经完成整套运行；现在收尾更新文档、提交结果，并同步 GitHub 和服务器。

## 产物与哈希

以下完整产物已保存本地和服务器，runs/ 不进入普通 Git；克隆仓库时需另行同步原始产物。

- [模型运行 metrics](../../runs/20260911_140804_nvidia_full_suite/metrics.json)
- [模型运行 manifest](../../runs/20260911_140804_nvidia_full_suite/manifest.json)
- [设备显存采样汇总](../../runs/20260911_140804_nvidia_full_suite_control/gpu_summary.json)
- [参考实现 CPU 对照 metrics](../../runs/20260911_193510_evaluator_reference_control/metrics.json)
- [逐题 CSV（附参考对照标记）](../../runs/20260911_140717_full_suite_session/testcase_assessment.csv)
- [评测条件说明](../../runs/20260911_140717_full_suite_session/assessment.json)

```text
模型 metrics       ee24d404d750292f63933c2cbd848c20bcc0d73e0b72abe2f7ad1e7bf6632c6f
模型 manifest      89dcf70893744c569ec75513ed3bd9c969ec49b29bd3415a789c6b7ff3b15d2c
显存汇总            b94a24e1f7529211cd34675d9a6488152e2043aeafcca63e6c678c51b5053dab
参考对照 metrics   69eff09a7bfd5e4d8097f09b15443a290b53c2e3acae13001078e01655441f08
参考对照 manifest  de29191d514061328bdd3bd444609742e104911ef842ae255b78ad1df972d83c
逐题评测说明 CSV    c141a762bfb0c1335234ff049aa5ec393334fc4003cadc80235ec8c508509d3d
```

## 本次文档变更与验证边界

- 更新 README、AGENTS、三份共识文档和模型清单；保存原三题部署 smoke 证据并新增全量记录。
- 实测源码和运行配置保持 0870769 版本；本轮收尾只修改文档与模型结果登记，不修改模型身份。
  已完成的 22 项 pytest 证据仍适用于该版本，没有为纯结果归档重新跑 GPU 或无关回归。
- 因实际发现参考输入编译失败，新增上述 156 题 CPU 对照，这是评测适用性检查，不能混入模型通过率。
- 原始任务已完成：两个 4B 模型、一条脚本、完整 156 题、可见逐题与最终结果，Git 归档。
  后续工作为评测条件修复、模型失败分析及同权重裸跑对照；自有 Docker、AMD、Vivado 仍未验收。

## 完整逐题表

“参考对照”是单独 CPU 实验的状态；该列为 FAIL 的五题需要结合前述限制解释。

| Testcase | 原始独立结果 | 生成轮数 | 用时（秒） | 原始失败原因 | 参考对照 |
| --- | --- | --- | --- | --- | --- |
| Prob001_zero | PASS | 1 | 18.03 |  | PASS |
| Prob002_m2014_q4i | PASS | 1 | 13.41 |  | PASS |
| Prob003_step_one | PASS | 1 | 11.94 |  | PASS |
| Prob004_vector2 | PASS | 1 | 59.42 |  | PASS |
| Prob005_notgate | PASS | 1 | 14.83 |  | PASS |
| Prob006_vectorr | PASS | 1 | 20.96 |  | PASS |
| Prob007_wire | PASS | 1 | 13.80 |  | PASS |
| Prob008_m2014_q4h | PASS | 1 | 14.08 |  | PASS |
| Prob009_popcount3 | PASS | 1 | 20.59 |  | PASS |
| Prob010_mt2015_q4a | PASS | 1 | 13.74 |  | PASS |
| Prob011_norgate | PASS | 1 | 13.52 |  | PASS |
| Prob012_xnorgate | PASS | 1 | 17.06 |  | PASS |
| Prob013_m2014_q4e | PASS | 1 | 14.60 |  | PASS |
| Prob014_andgate | PASS | 1 | 13.10 |  | PASS |
| Prob015_vector1 | PASS | 1 | 16.58 |  | PASS |
| Prob016_m2014_q4j | PASS | 1 | 16.66 |  | PASS |
| Prob017_mux2to1v | PASS | 1 | 21.40 |  | PASS |
| Prob018_mux256to1 | PASS | 1 | 18.00 |  | PASS |
| Prob019_m2014_q4f | PASS | 1 | 17.26 |  | PASS |
| Prob020_mt2015_eq2 | PASS | 1 | 15.81 |  | PASS |
| Prob021_mux256to1v | PASS | 1 | 23.95 |  | PASS |
| Prob022_mux2to1 | PASS | 1 | 15.86 |  | PASS |
| Prob023_vector100r | PASS | 1 | 19.75 |  | PASS |
| Prob024_hadd | PASS | 1 | 17.46 |  | PASS |
| Prob025_reduction | PASS | 1 | 13.62 |  | PASS |
| Prob026_alwaysblock1 | PASS | 1 | 20.33 |  | PASS |
| Prob027_fadd | PASS | 1 | 20.49 |  | PASS |
| Prob028_m2014_q4a | PASS | 2 | 75.28 |  | PASS |
| Prob029_m2014_q4g | PASS | 1 | 18.61 |  | PASS |
| Prob030_popcount255 | PASS | 3 | 200.65 |  | PASS |
| Prob031_dff | PASS | 1 | 19.13 |  | PASS |
| Prob032_vector0 | PASS | 1 | 27.63 |  | PASS |
| Prob033_ece241_2014_q1c | PASS | 3 | 86.21 |  | PASS |
| Prob034_dff8 | PASS | 1 | 16.20 |  | PASS |
| Prob035_count1to10 | PASS | 1 | 20.17 |  | PASS |
| Prob036_ringer | PASS | 1 | 18.98 |  | PASS |
| Prob037_review2015_count1k | PASS | 1 | 19.20 |  | PASS |
| Prob038_count15 | PASS | 1 | 21.56 |  | PASS |
| Prob039_always_if | PASS | 1 | 21.96 |  | PASS |
| Prob040_count10 | PASS | 1 | 19.99 |  | PASS |
| Prob041_dff8r | PASS | 1 | 17.61 |  | PASS |
| Prob042_vector4 | PASS | 1 | 26.51 |  | PASS |
| Prob043_vector5 | FAIL | 3 | 141.65 | output_mismatch | PASS |
| Prob044_vectorgates | PASS | 2 | 52.28 |  | PASS |
| Prob045_edgedetect2 | PASS | 1 | 23.94 |  | PASS |
| Prob046_dff8p | PASS | 1 | 19.19 |  | PASS |
| Prob047_dff8ar | PASS | 1 | 26.48 |  | PASS |
| Prob048_m2014_q4c | FAIL | 1 | 18.71 | output_mismatch | PASS |
| Prob049_m2014_q4b | PASS | 1 | 20.51 |  | PASS |
| Prob050_kmap1 | PASS | 1 | 20.85 |  | PASS |
| Prob051_gates4 | PASS | 3 | 152.82 |  | PASS |
| Prob052_gates100 | PASS | 1 | 27.61 |  | PASS |
| Prob053_m2014_q4d | FAIL | 3 | 58.44 | output_mismatch | PASS |
| Prob054_edgedetect | FAIL | 3 | 68.94 | output_mismatch | PASS |
| Prob055_conditional | PASS | 1 | 16.91 |  | PASS |
| Prob056_ece241_2013_q7 | FAIL | 2 | 49.66 | output_mismatch | PASS |
| Prob057_kmap2 | FAIL | 3 | 89.89 | output_mismatch | PASS |
| Prob058_alwaysblock2 | PASS | 1 | 30.52 |  | PASS |
| Prob059_wire4 | PASS | 1 | 28.70 |  | PASS |
| Prob060_m2014_q4k | PASS | 1 | 20.87 |  | PASS |
| Prob061_2014_q4a | PASS | 1 | 21.96 |  | PASS |
| Prob062_bugs_mux2 | FAIL | 1 | 18.33 | output_mismatch | PASS |
| Prob063_review2015_shiftcount | FAIL | 3 | 72.34 | output_mismatch | PASS |
| Prob064_vector3 | PASS | 1 | 43.32 |  | PASS |
| Prob065_7420 | PASS | 1 | 30.53 |  | PASS |
| Prob066_edgecapture | FAIL | 2 | 51.67 | output_mismatch | PASS |
| Prob067_countslow | PASS | 2 | 36.46 |  | PASS |
| Prob068_countbcd | PASS | 3 | 138.10 |  | PASS |
| Prob069_truthtable1 | PASS | 3 | 82.19 |  | PASS |
| Prob070_ece241_2013_q2 | FAIL | 3 | 94.90 | output_mismatch | PASS |
| Prob071_always_casez | PASS | 1 | 29.21 |  | PASS |
| Prob072_thermostat | PASS | 1 | 22.60 |  | PASS |
| Prob073_dff16e | FAIL | 1 | 28.57 | output_mismatch | PASS |
| Prob074_ece241_2014_q4 | FAIL | 3 | 110.86 | output_mismatch | PASS |
| Prob075_counter_2bc | PASS | 1 | 29.23 |  | PASS |
| Prob076_always_case | PASS | 1 | 29.62 |  | PASS |
| Prob077_wire_decl | PASS | 1 | 23.69 |  | PASS |
| Prob078_dualedge | PASS | 3 | 71.70 |  | PASS |
| Prob079_fsm3onehot | PASS | 3 | 106.17 |  | PASS |
| Prob080_timer | PASS | 3 | 74.46 |  | PASS |
| Prob081_7458 | PASS | 1 | 32.48 |  | PASS |
| Prob082_lfsr32 | FAIL | 3 | 80.20 | testbench_timeout | FAIL |
| Prob083_mt2015_q4b | PASS | 3 | 67.62 |  | PASS |
| Prob084_ece241_2013_q12 | PASS | 3 | 84.34 |  | PASS |
| Prob085_shift4 | PASS | 1 | 25.27 |  | PASS |
| Prob086_lfsr5 | FAIL | 3 | 70.64 | compile_failed | PASS |
| Prob087_gates | PASS | 1 | 21.25 |  | PASS |
| Prob088_ece241_2014_q5b | PASS | 2 | 79.29 |  | PASS |
| Prob089_ece241_2014_q5a | PASS | 3 | 85.35 |  | PASS |
| Prob090_circuit1 | PASS | 1 | 17.16 |  | PASS |
| Prob091_2012_q2b | PASS | 3 | 84.16 |  | PASS |
| Prob092_gatesv100 | PASS | 1 | 35.68 |  | PASS |
| Prob093_ece241_2014_q3 | FAIL | 3 | 108.58 | output_mismatch | PASS |
| Prob094_gatesv | FAIL | 3 | 129.30 | output_mismatch | PASS |
| Prob095_review2015_fsmshift | FAIL | 3 | 76.54 | output_mismatch | PASS |
| Prob096_review2015_fsmseq | FAIL | 1 | 58.62 | output_mismatch | PASS |
| Prob097_mux9to1v | PASS | 1 | 54.16 |  | PASS |
| Prob098_circuit7 | PASS | 1 | 19.79 |  | PASS |
| Prob099_m2014_q6c | FAIL | 2 | 133.09 | compile_failed | FAIL |
| Prob100_fsm3comb | PASS | 1 | 24.20 |  | PASS |
| Prob101_circuit4 | PASS | 1 | 87.21 |  | PASS |
| Prob102_circuit3 | FAIL | 3 | 68.06 | output_mismatch | PASS |
| Prob103_circuit2 | FAIL | 2 | 84.76 | output_mismatch | PASS |
| Prob104_mt2015_muxdff | FAIL | 3 | 87.12 | compile_failed | PASS |
| Prob105_rotate100 | FAIL | 3 | 97.09 | output_mismatch | PASS |
| Prob106_always_nolatches | PASS | 1 | 34.44 |  | PASS |
| Prob107_fsm1s | PASS | 1 | 27.94 |  | PASS |
| Prob108_rule90 | FAIL | 3 | 215.70 | compile_failed | PASS |
| Prob109_fsm1 | PASS | 1 | 30.24 |  | PASS |
| Prob110_fsm2 | PASS | 1 | 34.49 |  | PASS |
| Prob111_fsm2s | PASS | 1 | 24.68 |  | PASS |
| Prob112_always_case2 | PASS | 3 | 93.81 |  | PASS |
| Prob113_2012_q1g | FAIL | 3 | 103.73 | output_mismatch | PASS |
| Prob114_bugs_case | PASS | 3 | 104.84 |  | PASS |
| Prob115_shift18 | FAIL | 3 | 103.84 | output_mismatch | PASS |
| Prob116_m2014_q3 | FAIL | 3 | 95.85 | output_mismatch | PASS |
| Prob117_circuit9 | PASS | 3 | 68.75 |  | PASS |
| Prob118_history_shift | PASS | 1 | 32.05 |  | PASS |
| Prob119_fsm3 | PASS | 2 | 89.75 |  | PASS |
| Prob120_fsm3s | PASS | 1 | 45.53 |  | PASS |
| Prob121_2014_q3bfsm | PASS | 1 | 43.06 |  | PASS |
| Prob122_kmap4 | FAIL | 3 | 105.05 | compile_failed | PASS |
| Prob123_bugs_addsubz | PASS | 1 | 24.09 |  | PASS |
| Prob124_rule110 | FAIL | 3 | 130.96 | output_mismatch | PASS |
| Prob125_kmap3 | FAIL | 3 | 192.31 | output_mismatch | PASS |
| Prob126_circuit6 | PASS | 1 | 22.28 |  | PASS |
| Prob127_lemmings1 | PASS | 1 | 28.92 |  | PASS |
| Prob128_fsm_ps2 | FAIL | 3 | 95.67 | output_mismatch | PASS |
| Prob129_ece241_2013_q8 | PASS | 1 | 36.19 |  | PASS |
| Prob130_circuit5 | PASS | 1 | 25.29 |  | PASS |
| Prob131_mt2015_q4 | FAIL | 2 | 60.02 | output_mismatch | PASS |
| Prob132_always_if2 | PASS | 1 | 23.23 |  | PASS |
| Prob133_2014_q3fsm | FAIL | 3 | 150.68 | output_mismatch | PASS |
| Prob134_2014_q3c | FAIL | 3 | 124.72 | compile_failed | PASS |
| Prob135_m2014_q6b | FAIL | 3 | 97.71 | output_mismatch | PASS |
| Prob136_m2014_q6 | FAIL | 3 | 105.79 | output_mismatch | PASS |
| Prob137_fsm_serial | PASS | 3 | 348.29 |  | PASS |
| Prob138_2012_q2fsm | PASS | 1 | 66.76 |  | PASS |
| Prob139_2013_q2bfsm | PASS | 1 | 75.60 |  | PASS |
| Prob140_fsm_hdlc | PASS | 3 | 183.69 |  | PASS |
| Prob141_count_clock | FAIL | 2 | 86.79 | testbench_timeout | FAIL |
| Prob142_lemmings2 | PASS | 3 | 145.61 |  | PASS |
| Prob143_fsm_onehot | FAIL | 3 | 261.56 | output_mismatch | PASS |
| Prob144_conwaylife | FAIL | 3 | 260.03 | compile_failed | PASS |
| Prob145_circuit8 | FAIL | 3 | 85.15 | output_mismatch | PASS |
| Prob146_fsm_serialdata | FAIL | 3 | 351.74 | output_mismatch | PASS |
| Prob147_circuit10 | PASS | 3 | 89.96 |  | PASS |
| Prob148_2013_q2afsm | PASS | 1 | 41.23 |  | PASS |
| Prob149_ece241_2013_q4 | FAIL | 3 | 222.79 | output_mismatch | PASS |
| Prob150_review2015_fsmonehot | FAIL | 3 | 138.57 | output_mismatch | PASS |
| Prob151_review2015_fsm | FAIL | 3 | 165.79 | compile_failed | FAIL |
| Prob152_lemmings3 | FAIL | 3 | 183.19 | output_mismatch | PASS |
| Prob153_gshare | FAIL | 3 | 260.03 | compile_failed | PASS |
| Prob154_fsm_ps2data | PASS | 3 | 135.95 |  | PASS |
| Prob155_lemmings4 | PASS | 3 | 220.07 |  | PASS |
| Prob156_review2015_fancytimer | FAIL | 3 | 207.40 | compile_failed | FAIL |

## 提交前验证与发布

- 9 份文档及模型结果登记文件已暂存；git diff --cached --check 通过。
  凭据模式、单文件大小和大型产物边界检查通过，没有暂存 runs/、权重或环境。
- 模型身份与 HEAD 完全一致，原三题验证证据完整保留；文档中的本地链接核对通过。
  自有源码、运行配置、测试、Docker、入口和两个子模块均没有本轮改动。
- 服务器同步后的 testcase_assessment.csv 和参考对照 metrics SHA256 与本地一致；GPU 再查为 1 MiB / 0%。
- git fetch origin 后，HEAD..origin/main 无新增提交，沿现有历史正常提交推送。
  本日志自身的结果提交通过 Git 历史追溯，不为了写入自身 SHA 形成循环提交。

助手用户可见回复原文：

> 结果核对已完成，逐题表已附上 5 道评测异常题的标记。代码、权重版本和运行参数与本次实测一致；正在提交文档和结果清单，原始日志已在本地与服务器各保留一份。

发布核对通过后使用的答复文本：

> **156 题已全部跑完，结果已推送到仓库。**
>
> - 原始结果：**109 题通过、47 题未通过，通过率 69.87%**；执行错误和漏跑均为 0。
> - 耗时约 **3 小时**，显存采样最大 **29.49 GiB**。
> - 有 **5 题存在评测条件问题**，已在逐题记录中单独标记。
>
> 服务器上一行重跑：`./run.sh --suite verilogeval-v2`。
