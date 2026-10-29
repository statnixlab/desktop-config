# WPS、AB Download Manager 与微信的可选兼容安装

默认桌面恢复不启用这组应用专用显示服务。安装应用本体后，用仓库根目录的
`scripts/install-app-compat.py --wps --abdownloadmanager --wechat --apply` 按需选择。
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

## 微信

安装目标为官方 Linux 微信 `/opt/wechat/wechat`，本机核验版本为 `wechat-bin 4.1.13.26-1`。
用户桌面入口调用 `chat-hidpi-launch wechat`，以 `QT_QPA_PLATFORM=xcb` 启动。在所有活动
显示器均为 200% 的 Niri 会话中，微信使用独立的 `xwayland-wechat.service`（`:4`），
保留共享内存渲染 `-glamor none`、光标比例和 Fcitx5 连接。QQ／AB 继续使用原 `:2` 服务。
其他缩放使用原 `DISPLAY`，不启用这一组 200% 专用设置。

```bash
python3 scripts/install-app-compat.py --wechat
python3 scripts/install-app-compat.py --wechat --apply
```

微信专用桥接从公开上游加完整补丁重建，来源见 `../wechat-compat/source.json`。
`XWS_FILE_CLIPBOARD_EXE=/opt/wechat/wechat` 限定请求进程：文件管理器复制文件时，只向微信
展示文件 URL 格式，避免把同一剪贴板里的纯文本路径粘进输入框。原始文件列表和字节不变，
普通文字／图片及其他进程的格式列表保持原样。没有进程内注入，也没有临时剪贴板接管程序。

本机已由用户确认：重新复制文件后微信出现附件，随后复制新文字能正常更新，QQ 文件粘贴
仍正常。独立测试覆盖请求进程范围、属性长度查询、文件到文字切换及原始数据保持。
XWayland／共享内存显示方案继续保留；真实息屏唤醒的长期表现仍需观察。

安装器不会关闭微信或重启显示服务。安装后本人结束通话／传输并完全退出、重开微信。
输入法重新启动时会重新连接独立显示。此选项不复制聊天记录、账户、缓存或登录信息，
也不启用额外通知桥接。先前失败的进程内剪贴板试验不包含在安装流程中。

## 备份与单独构建

安装器备份已存在的配置和显示桥接至 `~/.local/state/desktop-config-backups/apps-*`。
运行中的显示服务不被重启。三个 `xwayland-*.service` 按启动器需要启动，AB 路径监视器会启用。

单独准备／检查源码，不构建或安装：

```bash
python3 scripts/build-app-compat.py wps --prepare-only
python3 scripts/build-app-compat.py chat --prepare-only
python3 scripts/build-app-compat.py wechat --prepare-only
```

`--target-home` 可用于临时目录验证；`--build-root` 可给应用安装器指定独立构建缓存。
已有构建目录若与固定源码／补丁不一致，程序停止，避免覆盖手工修改。
