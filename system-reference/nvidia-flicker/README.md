# 本机 4K 160Hz 下的 Niri 闪烁规避方案

**这是这台电脑上的实测情况。用户的另一台电脑使用相同系统和桌面环境，显示正常。**
另一台电脑的显卡、显示器、驱动及连接方式未在本次排查中逐项核对，因此不能将问题
归结为所有 CachyOS / Clavis / Niri 机器都会遇到的通用故障。

本目录只保存按需参考，默认安装、普通恢复和 `--same-hardware` 恢复都不会启用它。
两项新增开关默认关闭。正常的电脑无需应用此方案。

## 出现问题的机器

| 项目 | 排查时的状态 |
| --- | --- |
| 系统与内核 | CachyOS，7.2.10-1-cachyos |
| 显卡与驱动 | NVIDIA GeForce RTX 4070 SUPER，615.78.08，open kernel module |
| 显示器与连接 | P2710V，经 DisplayPort 连接，当前连接器 DP-1 |
| 输出 | 3840×2160 @ 160Hz，缩放 2，VRR 不可用 |
| 桌面 | Clavis + 本仓库锁定的定制 Niri，基准 `ed0fe6141a7cb82f23e947ec1e49bb6399ec9877` |
| 验证日期 | 2026-10-18 |

有应用的工作区右下方会快速闪出底色，应用未覆盖的区域较明显，受影响区域内的 Dock
也可能暂时不可见。120Hz 对照下闪烁消失；用户希望保留 160Hz。
临时改变 Niri 的 backdrop / 工作区底色后，闪块颜色也随之改变，但这不能单独确定
根因是合成器、驱动还是显示输出路径。

## 已验证的组合与边界

本机使用以下三项后，用户确认闪烁消失：

```kdl
debug {
    prefer-16bit-output
    restrict-primary-scanout-to-matching-format
    force-full-repaint
}
```

- 实际输出已核验为 **AB4H（16 位浮点缓冲），4K 160Hz，缩放 2**，运行的 Niri
  二进制与本次构建一致。
- 只开启 FP16 时仍闪；完整重绘与 FP16 的组合有效。**尚未单独测试关闭 FP16 后，
  仅完整重绘是否也有效**，因此不要把三项中某一项描述为已单独证明的根治方法。
- Plasma 对照中，“优先色彩精度”也使观察到的闪烁消失；此现象没有证明两个合成器
  的内部原因完全相同。
- 没有用锁频、驱动降级或覆盖通用配置实现规避。现有 Genie、HiDPI、输入法和
  PipeWire 兼容补丁均保留。截图/录屏仍使用原有独立格式；没有完成所有应用与游戏
  的长期回归测试。

## 开销

有重绘任务时会更新整个输出，增加 GPU 工作量、显存带宽，并可能增加缓冲分配；
它不会自行创建持续 160Hz 重绘。FP16 每像素 8 字节，单个 4K 缓冲约 63.3MiB，
此前 32 位格式约 31.6MiB。主平面直扫格式限制可能使部分全屏应用继续经过合成。
未做同负载 A/B 测量，不能给出准确的额外功耗、帧率或延迟百分比。

## 仅在需要复现时手动启用

本目录的配置入口会包含原 `config.kdl`，并追加上述三个开关，不复制本机 GPU 路径、
显示器布局或其他应用设置。已有同名文件时先对照合并，避免覆盖个人修改。
**已经在本机启用的现有入口无需重复安装。**

1. 核对硬件、Niri 基准提交和补丁版本，使用仓库的 `scripts/build-niri.sh` 构建。
   普通未打补丁的 Niri 不认识新增开关。
2. 将 `full-repaint-diagnostic.kdl` 放到 `~/.config/niri/`，与现有 `config.kdl` 同级。
   校验：

   ```bash
   ~/.local/lib/niri-desktop/niri validate --config ~/.config/niri/full-repaint-diagnostic.kdl
   ```

3. 将 `90-full-repaint-diagnostic.conf` 放到 `~/.config/systemd/user/niri.service.d/`，
   确认其余个人服务片段仍保留，再执行 `systemctl --user daemon-reload`。
   这份服务示例适用于本仓库的用户目录安装入口。
4. 保存工作，注销后重新进入 Niri。确认刷新率、实际缓冲格式和原先的复现场景，
   并检查模糊、截图/共享、最小化及常用应用。配置加载成功不等于所有硬件均适用。

## 停用与回退

在 Plasma 或 TTY 中操作，避免直接重启正在使用的桌面。先将示例服务片段移到
`niri.service.d/` 之外保存，再执行 `systemctl --user daemon-reload`；原来的
`60-niri-edge.conf` 会重新使用个人 `config.kdl`。若此前手动把三个开关加入主配置，
也应只移除这些行并重新校验，不要覆盖整个配置目录。

下次进入 Niri 即恢复普通入口。新增开关默认关闭，所以通常无需撤销编译补丁。
若需要恢复旧二进制，先确认它能解析当前个人配置，并使用对应的已保存备份。

## 参考

- [Niri 上游类似的高刷新率右下闪烁报告](https://github.com/niri-wm/niri/issues/2597)
- [NVIDIA 驱动问题讨论](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/801)

上游报告仅供对照，不能替代这台电脑的实测，也不能推断另一台正常电脑需要修改。
