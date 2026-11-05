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

## Niri 与 Smithay 源码维护（2026-11-03 起）

NVIDIA 台式机的完整 Niri 源码位于 `/home/nlh/.local/share/niri-source`，对应
`statnixlab/niri-edge` 的 `machine/nvidia-desktop` 分支。它从本机原有源码整理，
保留 NVIDIA 防闪烁、浮动层级、原生浮动最大化、独立模糊和高分屏动画修复。
源码整理时未迁移 AMD 标题栏双击行为。2026-11-04 单独迁入了
`599ad91`，启用 `titlebar-double-click-to-column` 后，标题栏双击切换列宽，
最大化按钮保持原生行为。NVIDIA 专用依赖和防闪设置继续保留。

`upstream` 追踪 `StatIndet/niri-edge`，`official` 追踪 `niri-wm/niri`。先 fetch，
再在独立审查分支合并上游并验证；完整流程见源码仓库的
`docs/PERSONAL-MAINTENANCE.md`。两个机器分支不得整体互相合并。

本机需要的 Smithay PR #2151 补丁已在 `statnixlab/smithay` 的
`machine/nvidia-desktop` 分支中保存，本地位于 `/home/nlh/.local/share/smithay-source`。
Niri 的 Cargo.toml 与 Cargo.lock 直接固定该提交，保留本机需要的防闪烁逻辑。

`sources.lock.json.niri.source_mode` 为 `git`。准备脚本直接检出固定的完整源码，
不再应用外部补丁，并拒绝覆盖错误分支、不同提交或未完成修改。
`scripts/build-niri.sh --prepare-only` 只做源码核验。
旧配方保留于 `legacy_niri_patch_recipe`，不用于当前构建。

保存更新时，按 Smithay（如有修改）、Niri、desktop-config 的顺序推送对应机器分支。
仅更新源码版本引用时不运行完整桌面 capture，不收集其他聊天或 Clavis 的未完成修改。
源码整理和发布不自动更新正在运行的合成器；构建、选择新版本和会话重启另行处理。
