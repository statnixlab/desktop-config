# 个人 CachyOS / Arch · Niri / Clavis 桌面

这个公开仓库保存当前桌面的可迁移配置、主题资源和安装脚本。桌面源码位于
[statnixlab/quickshell](https://github.com/statnixlab/quickshell/tree/personal/cachyos-niri)，
本仓库通过 `sources.lock.json` 固定 Clavis、定制 Niri、Smithay、key-cli 和 MacTahoe 图标的版本。

## 在另一台电脑上安装

目标系统需要先装好 **CachyOS 或 Arch Linux**、网络和显卡驱动。以日常用户运行：

```bash
sudo pacman -Syu --needed git python curl
git clone https://github.com/statnixlab/desktop-config.git
cd desktop-config
./scripts/setup-arch.sh
```

仓库公开，无需登录 GitHub。图形会话里的安装步骤优先使用 `pkexec` 密码框；
没有图形认证环境时在终端输入 sudo 密码。不要以 root 身份运行整个安装脚本。
软件包下载、Niri 的 Rust 编译和 Clavis 的 Qt 编译需要时间、网络以及数 GB 可用磁盘。

**换电脑使用上面的默认命令，不加 `--same-hardware`。** 显示器布局、主屏选择、
设备指标绑定及原机器的 GTK/X11 DPI 将重置，进入桌面后按新显示器设置缩放。
只有同一台电脑重装、且显示器不变时，才使用 `./scripts/setup-arch.sh --same-hardware`。

建议在新机器的 TTY 或其他桌面会话中安装。完成后退出当前会话，在登录界面选择
**Niri**；没有登录管理器时从 TTY 运行 `niri-session`。脚本不配置自动登录或磁盘休眠。

安装流程依次完成：

1. 校验快照并显示恢复计划，安装 Arch 依赖和固定版本的 key-cli。
2. 备份目标电脑已有的同名文件，再恢复桌面设置。
3. 编译固定版本的 `StatIndet/niri-edge` 并应用本仓库补丁；保留 Genie 最小化、
   HiDPI 坐标修复和 PipeWire SHM 屏幕共享修复，并构建固定版本的 Smithay 防闪补丁。
4. 安装固定提交的 MacTahoe 图标主题，编译并安装 Clavis 原生模块和 Niri Launchpad。
5. 校验 Niri 配置，启用 Clavis、剪贴板、Fcitx5 和主题同步服务。
   旧独立 `nyx-dock.service` 会被关闭，避免出现两个 Dock。

## 当前快照包含什么

| 部分 | 内容 |
| --- | --- |
| 原生 Dock | 固定应用、顺序、大小、放大、自动隐藏、窗口预览、最小化；通知数字角标和高 DPI 图标采样 |
| 应用菜单 | 基于 cccp00-cup 的 macOS Launchpad，适配 Niri 覆盖层、Clavis 壁纸、图标预加载和统一出场动画；支持 Dock 与单击 Win 呼出，沿用 `config/clavis/launchpad.json` 分组 |
| 顶部组件 | 最大化窗口上方出现浮窗时保持顶栏隐藏；托盘抽屉允许总览滚动与三指切换，并随导航收起 |
| 文件管理器 | 默认使用 Nautilus，保留浅绿色界面、紫灰色 Clavis-Reference 图标，以及防止 KDE GTK 同步覆盖的设置；安装脚本不再安装 Dolphin |
| 图标与字体 | MacTahoe-light；Inter＋苹方 UI，Maple Mono CN 等宽字体，Apple Emoji 与 Symbols Nerd Font Mono 回退 |
| 终端 | Kitty、Alacritty 和 Konsole 的配色、透明度、字体、按键与主题同步 |
| Niri | 快捷键、窗口规则、鼠标、光标、模糊和最小化动画；所有窗口关闭焦点框，设置窗口使用匹配的 23 像素圆角 |
| 应用效果 | 设置 → 通用 → 透明与模糊：分别调整聚焦／未聚焦窗口不透明度、应用背景模糊开关，以及应用和面板各自独立的 1–5 级模糊强度；自动保存并生效 |
| 输入法 | Fcitx5、雾凇拼音、跟随壁纸的候选框主题；保留仓库已有 Rime 快照 |
| 壁纸与组件 | 当前壁纸、头像、天气位置、桌面卡片和侧栏设置 |
| QQ / Manggo | 截图与翻译的辅助脚本、Niri 快捷键和 portal 注册 |
| 网盘 | 夸克网盘入口和挂载服务定义；账号在新机重新配置 |
| 本机兼容参考 | 微信/QQ 与 WPS 的 XWayland/输入法启动脚本、微信通知桥接、音量恢复、服务片段及 ChatGPT 启动修复 |

Dock 与应用菜单只保存应用入口，不会安装所有固定的软件。Chrome、QQ、微信、
WPS、Codex、腾讯会议等需另行安装；安装后的 desktop ID 不同时重新固定即可。
未安装的应用在菜单中隐藏，安装后会按保存的布局恢复。

没有上传登录密码、Cookie、API 密钥、SSH 密钥、GitHub/Codex 凭据、通知或剪贴板历史。
Rclone / OpenList 等账号需要在新电脑重新授权；网盘挂载服务不会自动启动。
字体和图标资源的许可证随资源保留；MacTahoe 从其固定的公开源码提交安装。

## 预览与分步安装

```bash
# 只显示计划，不写配置
python3 scripts/restore.py

# 试装到临时目录，不影响当前桌面
python3 scripts/restore.py --target-home /tmp/clavis-preview --apply

# 与 setup-arch.sh 相同的分步流程
./scripts/install-arch-dependencies.sh
./scripts/install-key-cli.sh
python3 scripts/restore.py --apply
./scripts/build-niri.sh
./scripts/install-icon-theme.sh
./scripts/build-clavis.sh
./scripts/build-launchpad.sh
./scripts/install-launchpad-keybinding.sh
./scripts/enable-services.sh
```

恢复程序会检查目标桌面是否正在运行。若需要覆盖正在使用的配置，应先退出 Niri，
或停止它列出的 Clavis、输入法和主题同步服务。旧文件保存在
`~/.local/state/desktop-config-backups/`，不会清空整个配置目录。

Clavis 源码默认放在 `~/.local/share/clavis-source`；用 `CLAVIS_SOURCE_DIR` 可以另选目录。
Niri 源码默认放在 `~/.local/share/niri-desktop-source`；用 `NIRI_SOURCE_DIR` 可以另选目录。
脚本拒绝覆盖已有的不同版本或本地修改。Niri 安装在用户目录，系统软件包保留，
运行中的 compositor 不会被脚本强制重启。

应用菜单源码和 GPL-3.0 许可证在 `components/launchpad/`，上游出处记录于该目录的
`UPSTREAM.md`。`clavis-launchpad.service` 在登录 Niri 时后台预加载应用、图标与壁纸；
它与 Clavis 共用布局文件，已有文件夹和排序不需要手动重建。安装/卸载应用后会刷新列表。
若需切回内置菜单，把 `~/.config/clavis/launchpad-backend.json` 的 `external` 改为 `false`，
再执行 `systemctl --user disable --now clavis-launchpad.service`。

Win 快捷键由 keyd 将左右 Win 的单击映射到 F13 的硬件键码；标准 XKB 映射将它解释为
`XF86Tools`，因此 Niri 同时兼容 `XF86Tools` 和 `F13`，打开应用菜单。
Win 与其他按键组合时保持原来的修饰键功能。单击需在 300ms 内松开，长按不打开菜单。
`install-launchpad-keybinding.sh` 安装 `/etc/keyd/clavis-launchpad.conf` 并启用 keyd；
如已有其他 keyd 配置，脚本会停止，避免覆盖已有映射。停用映射可运行
`pkexec systemctl disable --now keyd.service`。其他桌面若要使用同一单击动作，需绑定
键盘映射实际产生的 `XF86Tools`（部分映射为 `F13`）。

## 新机器上的差异

- 定制构建支持 Genie 最小化；当前快照选择 `window-minimize-effect "scale"`。
  必须完成 `build-niri.sh` 后才使用完整配置。
  普通发行版 Niri 可能尚不支持这个选项，不能只复制配置而跳过构建。
- 启用中文 UTF-8 locale（通常是 `zh_CN.UTF-8`）。网络、蓝牙、声卡驱动和休眠能力
  由新系统设置；除上述 keyd 规则外，仓库不自动覆盖 `/etc`、bootloader、resume 或硬件授权。
- 新电脑需要重新确认显示器缩放、布局、鼠标、功耗模式和合盖设置。
  `system-reference/` 保存原机器的电源、设备和应用兼容配置参考。
- QQ、微信、腾讯会议和 WPS 的专用二进制兼容环境不随配置上传。
  QQ 的 `Ctrl+Alt+A` 辅助流程会临时关闭其他屏幕；完成、取消或超时后恢复。
  QQ 应用内的截图按钮不会调用此流程。
- `~/.local/bin` 需要位于 PATH 前部；Niri 配置和服务使用已恢复的包装入口。

`system-reference/user-home/` 按 `config`、`bin`、`share` 保存额外的本机配置，Home
路径使用 `@HOME@` 占位符。它们纳入校验清单，但不会由 `restore.py` 自动安装或启用。
聊天/WPS 启动器依赖另行准备的定制 XWayland 二进制及显示器缩放设置；音量服务对应
JBL PS3500；图标刷新服务保留了旧独立 Dock 的调用，仅作历史配置参考。
`system-reference/chatgpt/` 保存本地启动补丁和 Pacman 钩子，仅匹配已核验的
`26.924.22138` 版本与归档哈希。其他版本使用前需要重新判断，仓库不包含应用归档、
登录数据或补丁运行时的备份。

## 2026-10-17 快照补充

Clavis 加入了 Dock 通知计数（最多显示 `99+`，打开应用后清零），计数基于桌面通知，
不是聊天应用内部的真实未读数。关闭弹窗不会清零，更新同一条通知不会重复累计。
主屏监控还会在最后一个活动输出断开时尝试恢复内置屏幕，且不覆盖保存的显示偏好。
Dock 右键菜单支持退出运行中的应用，以及应用桌面文件提供的新建窗口动作；
退出优先调用应用自身的托盘退出菜单，否则正常请求关闭该应用全部窗口，不强制结束进程。

字体文件另行获取，下载地址、版本和校验值在
[`system-reference/fonts/sources.json`](system-reference/fonts/sources.json)。将对应的 TTF/TTC
安装到 `~/.local/share/fonts/` 后执行 `fc-cache -f`；Inter ZIP 使用 `extras/ttf/Inter-*.ttf`，
Maple ZIP 使用其中的 TTF。保留各字体来源的许可证。未安装这些字体时会使用现有回退字体。
VS Code 的字体设置单独保存在该目录，只合并字体选项，不覆盖其他编辑器配置。

Manggo 1.1.1 的 Wayland 顶部拖动兼容源码在
[`system-reference/manggo/`](system-reference/manggo/)，对应的用户启动器、自启和桌面入口在
`system-reference/user-home/`。启动器只对已验证的应用文件哈希加载补丁，应用升级后需重新核验。
微信／QQ 的 XWayland 高 DPI 与最小化转发完整补丁、基准提交在
[`system-reference/xwayland-satellite/`](system-reference/xwayland-satellite/)。
这些是本机兼容参考，不由默认安装流程启用，也不包含商业应用或字体二进制。

## 仅本机启用的显示兼容方案

2026-10-24，在这台 **RTX 4070 SUPER / P2710V、4K 160Hz** 电脑上，用户确认
Smithay PR #2151 的上一帧缓冲保留补丁消除了右下区域闪烁；日志确认使用 AB30 输出，
此前的 FP16 与完整重绘规避已关闭。Orca 恢复 GPU 加速后，用户再次确认修复可行。
**另一台使用相同系统和桌面环境的电脑显示正常**；这不是给所有机器启用的通用默认设置。

硬件、版本、实测边界、代价和按需启停方法见
[`system-reference/nvidia-flicker/`](system-reference/nvidia-flicker/)。相关补丁包含在
定制 Niri 中，但新开关默认关闭；普通恢复和 `--same-hardware` 都不会安装或启用
该目录中的配置入口、服务片段。

## 2026-10-23 配置快照

本次记录顶栏厚度与胶囊尺寸、Win+Tab 窗口缩略图总览、独立的应用/面板模糊、
通知弹窗限制，以及当前主题、输入法、鼠标和启动台布局。Clavis 源码版本由
`sources.lock.json` 固定；定制 Niri 补丁同时包含标题栏列宽切换和刷新率相关策略。

采集程序将 GPU 固定路径与闪烁规避开关保存在 `system-reference/user-home/`，
通用配置不会启用它们。该目录也保留本机的 Niri 入口链、Nautilus 文件选择器兼容
后端及其服务，恢复前需按当前硬件和软件版本核对；通用文件选择器使用 GNOME/GTK。
当前密码存储接口使用 KWallet，仓库不保存密钥环、密码或远程连接凭据。
微信提示音依赖本机的 `~/.local/share/sounds/clavis/wechat-classic.wav`，该应用音频
不随公开源码发布；需要此功能时在目标机器自行准备，并安装 `libcanberra`。

## 灵动岛快速访问

点击灵动岛后进入“快速访问”。在 Nautilus 中打开文件夹并按 `Ctrl+D` 添加书签，
灵动岛会自动同步 `~/.config/gtk-3.0/bookmarks`，保留自定义名称和顺序；书签改名、
移除也会同步。带书签标记的项目在 Nautilus 中管理，灵动岛只读这份书签文件。

“添加文件夹”保留独立快捷入口，保存到 `~/.config/clavis/quick-access.json`；
移除入口不会删除目录。选择窗口的“磁盘”区域列出已挂载到 `/mnt/`、`/media/`、
`/run/media/` 的分区，包括 Windows 文件夹，也可以通过“文件系统”或 `Ctrl+L`
输入路径。恢复书签不会自动挂载分区或连接网盘，目标路径需要先可用。

## 2026-10-24 配置快照

Niri 基线更新至 `StatIndet/niri-edge` 的 `b2aaeb3`，Smithay 更新至 `79bbed5`。
保留全部个人补丁和 Smithay #2151 防闪烁开关；已由上游包含的 SHM 录屏、
Genie HiDPI 修复不再重复携带。标题栏、独立模糊与旧防闪烁回退选项继续保留。

新增可复现的 Smithay #2151 补丁、Niri 配置开关及依赖锁定；新开关默认关闭，
按需启用的本机入口和实测记录保存在 `system-reference/nvidia-flicker/`。
`build-niri.sh --prepare-only` 可以只获取并校验两份源码与补丁，不编译或安装。
若已有 Niri 源码包含不同修改，指定新的 `NIRI_SOURCE_DIR`，构建脚本不会覆盖它。

Clavis 固定到包含 OpenList 托盘图标修复的提交，并保留之前的灵动岛文件夹快速访问、
书签同步、窗口总览、独立模糊和顶栏定制。同步当前启动台布局、最小化动画、输入法
通知设置、微信启动与通知桥接脚本。Orca 的启动器已恢复 GPU 加速。

另保存默认应用文件图标生成器、MIME 关联、空白右键新建模板、Zotero/ArtCraft 入口、
Tailscale 托盘和 ydotool socket 配置参考，见
[`system-reference/desktop-extras/`](system-reference/desktop-extras/)。应用数据与程序二进制不包含在快照中。

## 2026-10-26 配置快照

Clavis 更新到通知应用图标补全和 CPU/GPU 独立功耗显示版本；同步 Dock 排列、
Niri 中文快捷键说明、默认应用关联和 ArtCraft 应用入口版本。Fcitx5 的两类
Wayland 诊断通知隐藏设置继续保留。

Nautilus 右键新增“复制路径”和“复制当前文件夹路径”，多选时每行一个路径。
扩展位于 `share/nautilus-python/extensions/copy_path.py`，随默认恢复安装；
依赖 `nautilus-python`、GTK4 和 `wl-clipboard`，Arch 依赖脚本已包含这些包。
当前扩展适用于 Nautilus 4.1 扩展接口，恢复后重新打开 Nautilus 加载。

本机云盘远端选择与主题同步服务生命周期作为按需合并参考保留，见
[`system-reference/desktop-extras/`](system-reference/desktop-extras/)。
代理策略只保存[脱敏模板](system-reference/proxy-policy/README.md)，不包含账号、
订阅链接、节点地址或密钥。此快照不包含 NVIDIA 防卡顿频率服务及其开机重试修改；
此前已发布的 Smithay 防闪烁补丁和配置参考保持原状。

## 2026-10-26 后续桌面快照

Clavis 固定到 `bb7279c`，保存以下源码和当前生效设置：

- 灵动岛 Full display、媒体标题显示、上下双行网速，以及 CPU 温度／内存占用上下排列；
  文件夹快速访问、Nautilus 书签和个人仪表盘卡片继续保留。
- 顶栏显示与浮动开关、内外留白、占位偏移、圆角及名称／数值控制。当前顶栏为 39 像素，
  胶囊为 37 像素，内边距 3、内嵌边距 0、模块圆角 12；灵动岛厚度为 37 像素。
- 原生浮动窗口视差启用侧栏跟随，平铺列跟随关闭；设置窗口使用左侧红黄绿按钮，
  最大化操作适配定制 Niri。
- 顶栏保留平滑透明圆角；灵动岛主条使用独立的壁纸模糊背景，由 Niri 的几何圆角平滑裁边。
  配套的 `clavis-keystone-backdrop-*` 图层规则随 `config/niri/clavis/effects.kdl` 保存。
- 日历跨天刷新、应用图标查找、滑块动画和搜索高亮修复，以及最新空闲休眠处理。
- 启动台的“远程”分组和新应用入口已同步。分组只保存应用 ID，不包含远程连接凭据。

WPS／Zotero 的代理服务、本机源文件覆盖项和来源版本见
[`system-reference/wps-zotero/`](system-reference/wps-zotero/README.md)；休眠兼容参考见
[`system-reference/power/`](system-reference/power/README.md)。这些参考不会由默认恢复自动启用。

本次 Clavis 原生构建通过，27 组 CTest 中 26 组通过；已有的 `display_preview_contracts`
仍在保存预览验证时超时。QML 检查通过，保留 726 条提示性警告，不能视为零警告验证。
桌面快照的 23 项测试通过；在临时 Home 中恢复后，Niri 配置语法校验通过。

## 2026-10-28 通用显示修复

Clavis 固定到 `c21ad7a`：左右顶栏复用独立模糊背景，并按设置的圆角由 Niri 平滑裁切；
灵动岛只绘制一次形状并统一生成阴影，修复中间残留药丸。电池数字保持可见，文件选择器
的延迟回调也已修复。配套顶栏背景规则已进入通用快照。硬件配置、NVIDIA 参考补丁与
另一台机器的休眠策略保持各自原有设置。

## 2026-10-28 锁屏动画修复

Clavis 固定到 `2092640`：圆形展开改用直接裁切着色器，并在动画开始前准备渲染资源，
修复右侧区域短暂停留的问题。壁纸与时钟仍一起从左上角展开，保留原有速度曲线和
850 毫秒时长。提交包含着色器源码及编译好的 QSB，更新 Clavis 即可，无须重编 Niri
或恢复整套桌面配置。AMD 本机已通过实际锁屏验证，其他 GPU 尚未实测。

## 刷新快照

先提交并推送 Clavis 源码，再运行：

```bash
python3 scripts/capture-current.py --apply
python3 -m unittest discover -s tests -v
python3 scripts/restore.py
git add .
git commit -m '更新个人桌面配置'
git push
```

采集程序只收集明确的桌面配置，将 Home 路径替换成安装时展开的占位符，并清空凭据字段。
它不停止输入法，也不新增当前 Rime 学习记录、账号库或应用数据。定制 Niri 的源码补丁
在 `patches/niri-desktop.patch`；`sources.lock.json` 同时记录补丁的 SHA-256。

## 验证范围

Niri Launchpad 的构建、交互回归测试、应用/分组模型测试和进程通信测试均通过；
已在当前 Niri 会话验证覆盖层显示、Dock 调用、关闭后的焦点恢复及原有分组保留。
2026-10-17 快照对应的 Clavis 构建和 26 项 CTest 通过；改动范围的 QML 检查完成，
存在 68 条提示性警告，尚未全部消除。
迁移仓库的 20 项测试及 ShellCheck 通过。
已从远程获取固定的 Niri 源码并验证补丁可完整应用，安装器下载的 SHA-256 也已核对。
在临时目录验证了不同用户名、含空格 Home 路径、原文件备份、原生 Dock 分组、主题
及硬件重置后的恢复结果；恢复后的 Niri 配置通过当前定制版的语法校验。
**尚未在另一台全新电脑实际执行完整安装和图形登录**；下载源、AUR 构建与新硬件驱动
仍会影响安装结果。验证命令均不安装软件或修改当前桌面。
