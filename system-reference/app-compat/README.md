# WPS 与 AB Download Manager 的可选兼容安装

默认桌面恢复不启用这组应用专用显示服务。安装应用本体后，用仓库根目录的
`scripts/install-app-compat.py --wps --abdownloadmanager --apply` 按需选择。
只传其中一个选项即可仅安装对应应用的兼容配置。

构建依赖：Rust/Cargo、GCC、pkgconf、clang、libxcb、xcb-util-cursor、xorg-xwayland、
jq、xorg-xrdb、libnotify。请通过图形 polkit 认证安装缺失依赖；正常桌面安装已覆盖多数依赖。
桥接源码固定在公开上游提交，补丁和 SHA-256 随仓库保存；不会下载来源不明的现成二进制。

## WPS

本机验证版本为 WPS 12.1.2.29183、x86_64，使用带 `client-maximize-to-column` 的定制 Niri。
桌面快照已包含这个配置及悬浮窗口独立升降、原生悬浮最大化补丁。

- 专用 `:3` 显示桥接保留 200% 光标、输入法连接、最小化、重复最大化请求去重和表格／文字工具栏分类。
- `40-alt-keytip-shm.conf` 使用 `-glamor none`，解决 Alt 快捷键提示层出现黑底，已由用户确认。
- 工具栏常驻 hook 由 `../wps-compat/sticky-toolbar.c` 在本机编译；启动器仅对已验证的
  `libkshell.so` SHA-256 加载，不改写 WPS 安装包中的库。其他版本会自动跳过该 hook。
- WPS 主窗口继承普通 50% 列宽和 Win+R 的 1/3、1/2、2/3 预设。
- 自动重绘试验服务已废弃，不在安装清单中。恢复程序不会启用它。

专用显示只在所有活动屏幕均为 200% 的 Niri 会话启用；不同缩放或其他桌面走普通 WPS 入口。
在非 200% 环境，本机验证过的弹窗／光标表现不作相同保证。新增服务不会强制关闭现有 WPS。
保存并完全退出所有 WPS 后重新打开，启动器会在没有 WPS 窗口时加载更新的显示桥接。

## AB Download Manager

应用默认位置为 `/opt/abdownloadmanager`。启动器复用聊天用的 `:2` 显示桥接，为 Java 设置
适当的缩放，修复齿轮弹窗消失、小字体和过大光标。只有统一 200% Niri 会话走该显示。

安装前退出 AB，避免应用关闭时覆盖设置。安装器只合并 `uiScale=null`、`autoStartOnBoot=false`，
其他下载设置、API 认证、目录和下载任务保持目标电脑原值。自启由独立的
`abdownloadmanager-compat.desktop` 管理，请勿再打开应用内自启。

浏览器清单由目标电脑的 AB／浏览器扩展自行生成。路径监视器只把已知的原版 NativeMessaging
可执行路径改为用户兼容入口；不上传浏览器 profile、扩展凭据或下载历史。

## 备份与单独构建

安装器备份已存在的配置和显示桥接至 `~/.local/state/desktop-config-backups/apps-*`。
运行中的显示服务不被重启。两个 `xwayland-*.service` 按启动器需要启动，AB 路径监视器会启用。

单独准备／检查源码，不构建或安装：

```bash
python3 scripts/build-app-compat.py wps --prepare-only
python3 scripts/build-app-compat.py chat --prepare-only
```

`--target-home` 可用于临时目录验证；`--build-root` 可给应用安装器指定独立构建缓存。
已有构建目录若与固定源码／补丁不一致，程序停止，避免覆盖手工修改。
