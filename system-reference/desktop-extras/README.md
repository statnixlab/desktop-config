# 2026-10-24 桌面附加配置

这些文件按本机现有方案保存，不由默认恢复流程启用。先安装目标应用，再按目标机器合并。

- `../user-home/libexec/default-app-icons.py` 与三个 `default-app-icons.*` 用户单元：
  根据 GIO 默认应用生成文件类型图标，继承 Clavis-Reference。依赖 Python GObject、GTK4
  以及已安装的应用图标；生成的图标软链接和运行状态不上传。安装脚本与用户单元后，
  手动运行生成器，再选择 Clavis-Default-Apps 图标主题，启用 `.path` 和 `.timer` 单元。
  通用桌面快照仍使用 Clavis-Reference；本机实际主题记录在
  `../user-home/config/nyx-desktop-style/desktop-preferences.json`。
- `templates/` 是检查过无正文内容、无作者信息的空白右键新建模板，可复制到
  `xdg-user-dir TEMPLATES` 返回的目录。新电脑的模板目录名称可能不同。
  不自动重新采集该目录，避免把后来加入的个人文档当配置上传。
- `../user-home/config/mimeapps.list` 保存默认应用关联；应用 desktop ID 必须在目标机器存在。
- Orca 启动器恢复默认 GPU 加速，同时保留原生 Wayland 和输入法参数；需要另装 Orca AppImage。
- Zotero 启动器保留 Windows 共用文献库的挂载检查；仓库不包含文献库、附件或登录信息。
- ArtCraft 系列只保存桌面入口，AppImage、图标和升级后的文件名需在目标机器核对。
- Tailscale 托盘服务和 ydotool 用户 socket 设置作为参考保存；不包含网络账户、登录状态，
  也不自动修改 `/dev/uinput` 权限。

所有 `user-home/` 文件中的 `@HOME@` 需替换为目标用户 Home。

## 2026-10-26 更新

- `cloud-preferences.json` 仅记录默认远端名称 `quark-openlist`，不包含 rclone
  账号或令牌。目标电脑先配置同名远端，再将该字段合并到 Clavis 的
  `ui-preferences.json`；通用快照仍清空该字段，避免引用不存在的账号配置。
- `../user-home/config/systemd/user/nyx-theme-sync.path` 保存当前主题同步监听
  随 Niri 会话启停的配置。按需替换后需重新加载用户单元，并从旧的
  `default.target` 启用关系迁移到 `niri.service`；不会自动应用。
- 默认邮件关联指向本机 Thunderbird 自动生成的 desktop ID；迁移时应重新选择
  目标电脑已安装的 Thunderbird 入口。ArtCraft 的 AppImage 版本入口已同步。
