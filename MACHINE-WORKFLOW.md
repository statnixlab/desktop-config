# 两台机器独立维护

| 机器 | 两个仓库使用的分支 |
| --- | --- |
| AMD HawkPoint 笔记本（nlh-cachy） | `machine/amd-laptop` |
| NVIDIA 台式机（cachyos） | `machine/nvidia-desktop` |

两台都使用 `~/.local/share/clavis-source` 和 `~/.local/share/desktop-config`。
`hardware/machine.json` 标明本分支归属；`sources.lock.json` 的 Clavis 分支和提交
只对应本机。旧 `main` / `personal/cachyos-niri` 保留共同历史，不作为机器分支的自动更新目标。

## 保存本机

先在本机 Clavis 仓库按问题拆分提交，完成必要检查；不要把功能修复与显卡、电源政策放在
同一提交。然后在本机配置仓库运行：

```bash
python3 scripts/capture-machine.py
python3 scripts/capture-machine.py --apply
```

第一条只显示计划，第二条只更新仓库快照，不安装、不重启桌面。它核对机器名和分支，要求
Clavis 工作区干净，并锁定对应源码版本。审查差异后提交配置分支，先推送 Clavis，再推送
引用该提交的配置分支。`git pull --ff-only` 只跟随当前机器的远程分支。

`config/` 等目录沿用原来的可迁移快照格式。`hardware/` 保存显示器信息；
`system-reference/machine/` 另存本机 Niri 入口、用户服务 drop-in 和已存在的电源/显卡配置，
清单记录实际运行的 Niri 路径、版本和哈希。这些只是参考，恢复器不会自动安装它们。
未采集的软件安装状态、系统全盘、用户数据和账号不能靠这个仓库恢复。

## 借鉴另一台的修复

```bash
git fetch origin
git log --oneline HEAD..origin/machine/nvidia-desktop   # 在 AMD 笔记本查看台式机
# 在台式机查看笔记本时，把上面的分支换成 machine/amd-laptop
git show <选中的提交>
git cherry-pick -x <选中的提交>
```

在干净工作区执行迁移；先确认依赖，再验证目标机器。不要整分支 merge，也不要直接用
另一台的配置快照覆盖本机。`cherry-pick -x` 留下来源提交，便于追踪两台已采纳哪些修复。
修改源码后重新采集本机配置，保持 lock 与源码一致。上游作者更新也分别评估，先合入
一台并验证，再决定另一台是否采用。

## 机器专用限制

AMD 分支禁止应用 NVIDIA 专用补丁、GPU pinning、retained-frame/Smithay #2151、
FP16/full-repaint/刷新阈值策略、NVIDIA 休眠参数和频率服务。NVIDIA 分支保留其自己的
兼容方案；AMD 上的删除或替代也不能直接套用到台式机。

本次分支拆分没有重新构建或安装 Niri。历史 `sources.lock.json` 的 Niri/Smithay 构建配方
仍是共享历史，不代表两台现在运行的是同一个二进制；实际运行信息看机器清单。
尤其 AMD 不得运行历史 `setup-arch.sh` / `build-niri.sh` 整套流程：它含 NVIDIA 补丁。
需要重装或升级时，先针对目标机器准备独立构建/恢复计划，再执行。

## Niri 源码维护（2026-11-03 起）

AMD 本机的完整 Niri 源码已放到 `/home/nlh/.local/share/niri-source`，对应
`statnixlab/niri-edge` 的 `machine/amd-laptop` 分支。niri-edge 与本机补丁已成为
同一条保留完整历史的 Git 分支，构建时不再额外应用补丁。

源码仓库的 `upstream` 指向 `StatIndet/niri-edge`，`official` 指向 `niri-wm/niri`。
更新时先 fetch，在临时审查分支合并需要的上游，再验证本机行为。维护说明和构建命令
见源码仓库的 `docs/PERSONAL-MAINTENANCE.md`。另一台机器的专用改动仍独立维护。

`sources.lock.json.niri` 直接锁定该源码仓库的完整提交，`source_mode` 为 `git`。
`scripts/build-niri.sh --prepare-only` 只核对和准备此提交，保留已有工作区；存在本地
改动、错误分支或版本不匹配时会停止，不重置代码。Smithay 使用 Cargo.lock 固定的
未打补丁版本。旧补丁配方保存在 `legacy_niri_patch_recipe` 中，仅供历史追溯。

保存更新时先推送 Niri 的 `machine/amd-laptop`，再更新和推送本配置仓库中的 Niri
提交引用。只有采集完整桌面快照时才运行 capture；仅更新 Niri 版本引用时不要把
Clavis 或其他聊天尚未完成的改动一并收集。源码合并和推送不会自动替换运行中的合成器。
