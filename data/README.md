# 数据

verilog_eval/ 是 NVlabs/verilog-eval 的固定版本子模块。
当前使用 dataset_spec-to-rtl：156 份题目、156 份参考实现、156 份测试台。

scripts/prepare_data.py 生成 processed/verilogeval_v2.jsonl 与清单。
生成输入只含 task_id、question 和接口空壳 ref_sv；官方参考逻辑和测试台留在原始数据中。
转换过程不会修改原始数据。processed/ 可由固定源版本重建，不直接提交生成数据。
