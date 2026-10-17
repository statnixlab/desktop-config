# 本机 XWayland 高 DPI 与最小化补丁

`source.json` 固定上游仓库、基准提交、构建特性和已安装程序的校验值。
`hidpi-minimize.patch` 包含完整的本地差异：保留 `XWS_CURSOR_SCALE=2` 的光标比例修正，
并将 X11 的 `WM_CHANGE_STATE/IconicState` 转发为 Wayland `set_minimized`。
它需要合成器支持最小化；本桌面的定制 Niri 已支持。

在独立的上游 checkout 检出 `source.json` 中的 `base_commit`，依次执行
`git apply --check`、`git apply` 应用该补丁，再执行：

```sh
cargo build --release --locked --features systemd
cargo test --locked --features systemd hidpi_cursor_tests
```

构建结果对应 `~/.local/libexec/xwayland-satellite-hidpi`。
先备份旧程序，再在退出对应聊天应用后替换；重新启动 `xwayland-chat.service` 会断开
QQ／微信的显示连接，因此不能在通话或未保存工作时直接重启。
现有服务与启动脚本在 `system-reference/user-home/`，默认恢复流程不安装这些参考文件。

上游采用 MPL-2.0；完整源码、许可证及声明请从 `source.json` 指定的仓库获取。
