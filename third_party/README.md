# 上游代码

chipmate/ 是 Git 子模块，固定到主仓库记录的提交。

初始阶段直接调用原版工作流，保留其许可和目录。我们的入口与适配放在 src/qiansai/。
后续内部修改使用有历史的 fork 或单独补丁，不在未记录的脏子模块上进行正式实验。

恢复：git submodule update --init --recursive。
